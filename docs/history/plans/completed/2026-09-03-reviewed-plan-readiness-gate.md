# Plan: reviewed-plan readiness gate

Backlog origin: `docs/history/backlog/2026-08-31-reviewed-plan-readiness-gate.md`

## Terms

- **Readiness validator**: the new fail-closed script `scripts/plan_readiness.py`;
  given a plan path, it checks the plan-repository readiness contract and exits 0
  only when every condition passes, otherwise printing the first failed condition.
- **Review artifact**: the review-round Markdown under `{reviews_dir}` named
  `<YYYY-MM-DD>-plan-review-<feature-slug>-r<N>.md` plus its sidecar
  `<same>.stats.json` written per `review-staging`.
- **Sidecar**: the `.stats.json` file beside a review artifact; readiness keys on
  its `source_digest`, `source_kind: "plan"`, and schema validity.
- **Feature slug**: the plan filename stem with its leading `YYYY-MM-DD-` prefix
  removed; the glob `{reviews_dir}/*-plan-review-<feature-slug>-r<N>.md` finds
  the plan's review artifacts.
- **Latest round**: the review artifact with the highest round suffix `r<N>` in
  its filename for that feature slug; ties across dates resolved by filename
  order (date prefix included). Never resolve latest by mtime.
- **Drafting mode**: conversational Plan Mode in a host UI: the agent may
  present a proposed plan but cannot save, review, or finalize the artifact.

## Assumptions

- assume the validator lives at `scripts/plan_readiness.py` and imports from
  `scripts/validate_review_staging.py` (same directory) instead of duplicating
  digest, schema, or readiness rules; basis: the backlog's explicit reuse rule
  and the existing single-file shared-script convention.
- assume the readiness conditions are exactly: plan file exists under the
  resolved `{plans_dir}`; a review artifact for the feature slug exists; the
  latest round's sidecar exists and passes schema validation; sidecar
  `source_kind` is `plan`; sidecar `source_digest` equals the current plan bytes
  digest (recipe `compute_source_digest` from `validate_review_staging.py`);
  the latest review Markdown reports `ready=yes` in its `## Summary` verdict;
  and `is_review_ready()` over the same Markdown is True; basis: backlog
  Suggested fix item 2 mapped one-to-one onto verified existing functions
  (`is_review_ready` line 643, `compute_source_digest`, `stats_sidecar_path`
  line 661), with schema validity, `source_kind`, and digest enforced through
  the staging validation entry (`validate_stats_sidecar`) called with
  `expected_digest` and `source_kind` explicitly so its skip-waiver cannot
  fire (r3 adjudication: `classify_sidecar_schema` is not imported by name;
  the shared entry owns schema classification).
- assume the `done` gate applies when the session's deliverable includes a plan
  file under `{plans_dir}`, with the recorded user-stop exception from the
  backlog acceptance criteria; basis: backlog AC bullet 3.
- assume host integration lands as a new `agents/hooks/plan-readiness/README.md`
  documenting the final-response limitation plus a `hooks_probe.py` capability
  row that reports the current state (UNSUPPORTED for every agent row because
  no adapter is wired by scope; hosts differ: Claude Code exposes a blocking
  Stop-adjacent event, Codex has no blocking final-response event today);
  basis: backlog Suggested fix item 4 and
  the existing `(agent, hook)` matrix in `scripts/hooks_probe.py`.
- assume skill-EDITS tasks (Tasks 2-5) are doc/gate-text changes validated by
  structural greps, not RED→GREEN code tasks; basis: this repo's skill files are
  Markdown instruction sets with no test runner beyond structural validation.

## Gist & Examples

Today, nothing mechanically prevents `execute-plan` from starting or `done`
from finalizing a plan-creation session whose plan never passed `review-plan`:
the skill-gate only gates writes to plan files, and a plan that never touched
disk (conversational Plan Mode) bypasses it entirely. The PROJ-688 session
produced and presented an unreviewed plan that was only honestly labeled a
draft after the user asked.

This plan adds three enforcement layers, each fail-closed:

1. **Drafting boundary** (`agents/skills/plans/SKILL.md`): Plan Mode is declared
   a drafting mode; a pre-finalization self-check with five exact questions
   forbids calling a plan ready for execution without review evidence.
2. **Mechanical readiness** (`scripts/plan_readiness.py` *(new)*): one command
   that answers "does the latest review of these exact plan bytes report
   ready=yes with zero unresolved blocking findings and a valid sidecar?".

   ```
   python3 scripts/plan_readiness.py docs/plans/<plan>.md   # exit 0 = ready
   # exit 1 = first failed condition printed, e.g.:
   # readiness FAILED: sidecar source_digest is stale (plan bytes changed after review r2)
   ```
3. **Boundary gates** (`agents/skills/execute-plan/SKILL.md`,
   `agents/skills/done/SKILL.md`): both invoke the validator before starting
   implementation, resp. finalizing a plan-creation session.

Edge cases driving the design:

- **Plan edited after a clean review**: the digest no longer matches, so
  readiness fails with a stale-digest reason; a fresh review round is required.
- **Valid-schema sidecar, wrong digest**: schema passes, digest fails; readiness
  fails (the required test scenario).
- **Review edited after validation** (the review artifact changes post-hoc):
  readiness is recomputed at every gate call, so the next call re-reads the
  artifact and its sidecar; a Markdown-only edit that breaks
  `ready=yes`/blocking consistency fails even though the sidecar is untouched.
- **Plan outside `{plans_dir}`**: rejected; paths resolve from
  `.ai-playbook/facts.md` TOML, never hardcoded.
- **Codex host**: no blocking final-response hook event exists today, so the
  probe records UNSUPPORTED and the execution/finalization gates carry the
  enforcement; this limitation is documented, not hidden.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every backlog Test scenario maps to a discriminating
  `--selftest` fixture in `scripts/plan_readiness.py`; no two fixtures pass and
  fail together.
- fail-closed behavior: every missing, malformed, stale, or negative state
  exits non-zero with a reason naming the first failed condition only.
- maintainability: zero duplicated digest/schema/readiness logic; the validator
  imports from `validate_review_staging.py`.
- test coverage: the accepted state plus every rejected-state fixture listed in
  Task 1 have fixtures, including a review edited after validation and a
  valid-schema/incorrect-digest sidecar.

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` exits 0.
- `python3 scripts/validate_review_staging.py --selftest` still exits 0
  (no regression to the reused validator).
- `python3 scripts/hooks_probe.py --selftest` exits 0, and the
  `python3 scripts/hooks_probe.py --all` table contains a `plan-readiness` row
  reporting UNSUPPORTED. (`--all` is not required to exit 0: pre-existing
  unrelated FAIL rows on a given host already drive its exit code, so the gate
  keys on table content, not process status.)
- The four skill files contain the pinned obligations (Validation Commands).
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0 from repo root.

The live end-to-end acceptance is the `selftest#accepted_state` fixture (a
fixture-built clean plan plus matching review artifact passes readiness with
exit 0); the plan file itself is deliberately NOT a validation target, because
execute-plan checkbox marks and review-reference lines legitimately mutate the
plan digest after the final review round and would make a self-referential
exit-0 gate unsatisfiable.

**Ship when:**
- None; all acceptance evidence is repository-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and
fix if valid):

**Production code:**
- `scripts/plan_readiness.py` *(new)*
- `scripts/hooks_probe.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/hooks/plan-readiness/README.md` *(new)*

**Tests:**
- `scripts/plan_readiness.py` `--selftest` fixture family *(new, same file)*

**Plan-related extension**; implementation and review may change files not listed
above. Treat a finding as in scope when it is **causally related to this plan**:
it implements or completes a plan task, fixes a regression introduced by plan
work, closes wiring or docs implied by an explicit must-fix change, or
contradicts a contract the plan changed. If the link to the plan is weak or
speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reused as-is; a finding here belongs to
  the validator-pass plan unless the readiness wiring itself breaks it.
- `agents/skills/execute-plan/` session-log or manifest behavior unrelated to
  the readiness gate.
- Any PROJ-688 product code or plan; explicitly out of scope per the backlog.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1

# 1. Selftests (validator, reused validator, probe)
python3 scripts/plan_readiness.py --selftest || { echo "FAIL: readiness selftest"; exit 1; }
python3 scripts/validate_review_staging.py --selftest || { echo "FAIL: staging validator selftest regression"; exit 1; }
python3 scripts/hooks_probe.py --selftest || { echo "FAIL: hooks probe selftest"; exit 1; }
test -f scripts/hooks_probe.py || { echo "FAIL: hooks probe missing"; exit 1; }
# --all exit code is host-dependent (pre-existing unrelated FAIL rows); gate on table content.
PROBE_OUT="$(python3 scripts/hooks_probe.py --all || true)"
printf '%s\n' "$PROBE_OUT" | grep -F "plan-readiness" | grep -qF "UNSUPPORTED" \
  || { echo "FAIL: probe table has no plan-readiness UNSUPPORTED row"; exit 1; }

# 2. Pinned obligations, one dedicated grep each (rule: dedicated greps, no context spillover).
grep -qF "DRAFTING mode, not a completed plan lifecycle" agents/skills/plans/SKILL.md \
  || { echo "FAIL: plans drafting rule missing"; exit 1; }
grep -qF 'Was `review-plan` invoked for this plan?' agents/skills/plans/SKILL.md \
  || { echo "FAIL: self-check Q1 missing"; exit 1; }
grep -qF "Does the sidecar digest match the final plan bytes?" agents/skills/plans/SKILL.md \
  || { echo "FAIL: self-check Q3 missing"; exit 1; }
grep -qF "must not describe the plan as ready for execution when any answer is negative" agents/skills/plans/SKILL.md \
  || { echo "FAIL: self-check negative-answer rule missing"; exit 1; }
grep -qF 'Does the latest Markdown review and `.stats.json` sidecar exist?' agents/skills/plans/SKILL.md \
  || { echo "FAIL: self-check Q2 missing"; exit 1; }
grep -qF 'Does the latest review report `ready=yes`?' agents/skills/plans/SKILL.md \
  || { echo "FAIL: self-check Q4 missing"; exit 1; }
grep -qF "Are there zero unresolved blocking findings?" agents/skills/plans/SKILL.md \
  || { echo "FAIL: self-check Q5 missing"; exit 1; }
grep -qF "scripts/plan_readiness.py" agents/skills/plans/SKILL.md \
  || { echo "FAIL: plans mechanical-counterpart reference missing"; exit 1; }
grep -qF "does not authorize deployment" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: execute-plan deployment-non-authorization note missing"; exit 1; }
grep -qF "scripts/plan_readiness.py" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: execute-plan readiness gate missing"; exit 1; }
grep -qF "report the first failed readiness condition" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: execute-plan gate-stop obligation missing"; exit 1; }
grep -qF "scripts/plan_readiness.py" agents/skills/done/SKILL.md \
  || { echo "FAIL: done finalization readiness gate missing"; exit 1; }
grep -qF "stop without finalization" agents/skills/done/SKILL.md \
  || { echo "FAIL: done recorded-stop exception missing"; exit 1; }
grep -qF "scripts/plan_readiness.py" agents/skills/review-plan/SKILL.md \
  || { echo "FAIL: review-plan integration point missing"; exit 1; }
grep -qF "feed the readiness validator" agents/skills/review-plan/SKILL.md \
  || { echo "FAIL: review-plan readiness-contract sentence missing"; exit 1; }
grep -qF "cannot block the final response" agents/hooks/plan-readiness/README.md \
  || { echo "FAIL: Codex limitation undocumented"; exit 1; }
test -f scripts/plan_readiness.py || { echo "FAIL: validator script missing"; exit 1; }

# 3. No hardcoded layout paths in the new validator (test -f pre-check first).
if test -f scripts/plan_readiness.py && grep -nE 'docs/plans/|docs/reviews/' scripts/plan_readiness.py; then
  echo "FAIL: validator hardcodes layout paths"; exit 1
fi

# 4. Compile check.
python3 -m py_compile scripts/plan_readiness.py || { echo "FAIL: validator does not compile"; exit 1; }

# 5. Hygiene scan anchored to repo root (cwd-dependent script).
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh ) || { echo "FAIL: hygiene scan"; exit 1; }
echo "ALL VALIDATION COMMANDS PASSED"
```

The `docs/plans/` occurrence inside check 3 is a checker literal scoped to
`scripts/plan_readiness.py` only; the plan document is not swept and must not be
added to that sweep (its mentions are the gate's own text, not stale references).

### Task 1: Readiness validator with full accepted/rejected fixture matrix

Files:
- `scripts/plan_readiness.py` *(new)*

- [x] Run → expect RED: `python3 scripts/plan_readiness.py --selftest` exits
  non-zero because the script does not exist yet
- [x] Write `scripts/plan_readiness.py`: argparse CLI `plan_readiness.py
  <plan-path>` plus `--selftest`; resolve `{plans_dir}` and `{reviews_dir}` from
  the `.ai-playbook/facts.md` TOML block (reuse `scripts/facts_paths.py`);
  import `compute_source_digest`, `is_review_ready`, `stats_sidecar_path`,
  and the staging validation entry from `validate_review_staging.py`;
  call the staging entry with `expected_digest` and `source_kind` passed
  explicitly so its skip-waiver is disabled (r3 adjudication:
  `classify_sidecar_schema` is not imported by name; the shared entry owns
  schema classification); implement the readiness conditions from
  Assumptions in order, returning the first failed condition; never import or
  re-implement the digest recipe locally
- [x] Write the `--selftest` family covering every state, each fixture
  discriminating (built through a temp tree, not the live repo):
  - [x] `selftest#no_review_files`; given a plan under a temp `{plans_dir}` with
    no matching review artifact in the temp `{reviews_dir}`, expects exit 1 with
    a missing-review reason
  - [x] `selftest#missing_sidecar`; given the latest round Markdown present but
    no `.stats.json`, expects exit 1 with a missing-sidecar reason (Markdown
    alone must not be trusted)
  - [x] `selftest#malformed_sidecar`; given a `.stats.json` that is not valid
    JSON and one that fails `classify_sidecar_schema`, expects exit 1 with a
    malformed-sidecar reason
  - [x] `selftest#valid_schema_wrong_digest`; given a sidecar that passes schema
    validation but whose `source_digest` hashes different plan bytes, expects
    exit 1 with a digest-mismatch reason
  - [x] `selftest#stale_digest_after_plan_edit`; given a clean review, then the
    plan bytes edited, expects the next readiness call to exit 1 with a
    stale-digest reason (covers the "review edited after validation" and
    "plan edited after a clean review" backlog scenarios in both directions:
    edit the plan, and edit the review Markdown after a passing call so the
    following call re-reads it)
  - [x] `selftest#ready_no_verdict`; given a review whose Summary verdict is
    `ready=no` with zero blocking findings, expects exit 1 (verdict alone
    rejects)
  - [x] `selftest#unresolved_blocking_finding`; given `ready=yes` in Summary but
    one finding with `blocking: true` and no resolved triage value, expects
    exit 1 via `is_review_ready`
  - [x] `selftest#plan_outside_plans_dir`; given a plan path that resolves
    outside `{plans_dir}`, expects exit 1
  - [x] `selftest#missing_plan_path`; given a plan path that does not exist,
    expects exit 1 with a missing-plan reason
  - [x] `selftest#latest_round_selection`; given rounds r1 and r2 where r1 is
    clean and r2 is not (newer mtime on r1 to prove mtime is not used), expects
    the verdict of r2 to decide
  - [x] `selftest#accepted_state`; given a valid review whose sidecar digest
    matches the plan bytes, verdict is `ready=yes`, and no unresolved blocking
    findings, expects exit 0 and no reason output
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` exits 0
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py
  --selftest` still exits 0
- [x] Commit: `feat: add fail-closed plan readiness validator`

### Task 2: plans skill drafting-mode rule and pre-finalization self-check

Files:
- `agents/skills/plans/SKILL.md`

- [x] Add the drafting-mode rule (prescribed text, pinned by Validation
  Commands): "Conversational Plan Mode is a DRAFTING mode, not a completed plan
  lifecycle. When the conversation cannot save, review, and finalize the plan
  artifact, say that review and artifact finalization are pending."
- [x] Add the pre-finalization self-check with the five exact questions: "Was
  `review-plan` invoked for this plan?", "Does the latest Markdown review and
  `.stats.json` sidecar exist?", "Does the sidecar digest match the final plan
  bytes?", "Does the latest review report `ready=yes`?", "Are there zero
  unresolved blocking findings?"; followed by the closing rule: the agent "must
  not describe the plan as ready for execution when any answer is negative"
- [x] Reference `scripts/plan_readiness.py` as the mechanical counterpart the
  execution and finalization boundaries call
- [x] Run → expect GREEN: the eight plans-skill greps in Validation Commands pass
- [x] Commit: `skills: plans drafting-mode rule and pre-finalization readiness self-check`

### Task 3: execute-plan readiness gate at implementation start

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add a step in Phase 0 (before any task implementation): run the plan
  readiness gate, `python3 scripts/plan_readiness.py <plan-path>`; a non-zero
  exit is a hard gate: stop, report the first failed readiness condition, and
  require a fresh `review-plan` round after any plan edit (digest change)
  before re-execution
- [x] Note that a clean plan review establishes implementation readiness only;
  it does not authorize deployment, merge, or other external effects
- [x] Run → expect GREEN: the three execute-plan greps in Validation Commands pass
- [x] Commit: `skills: execute-plan hard gate on plan readiness before implementation`

Deviation note (adjudicated in review r2): the Step 0.5 gate as shipped
carries a mechanical resume exemption for checkbox-only plan drift
(`git log -p -- <plan-path>` evidence since the run's start, byte-identical
line remainders), replacing the broader carve-out originally prescribed
here; no pinned Validation Commands spans changed.

### Task 4: done finalization readiness gate with recorded-stop exception

Files:
- `agents/skills/done/SKILL.md`

- [x] Add a step before finalizing a plan-creation session: run
  `python3 scripts/plan_readiness.py <plan-path>`; refuse to finalize on
  failure, except when the user explicitly chooses to stop without
  finalization and that choice is recorded in the session log
- [x] Run → expect GREEN: both done greps in Validation Commands pass
- [x] Commit: `skills: done refuses to finalize a plan-creation session without plan readiness`

Deviation note (adjudicated in review r3): Step 1.5 as shipped is scoped to
this session's plan deliverables (untracked/modified relative to the session's
starting working-tree state, or named in the session log), excluding
`{plans_completed_dir}`, rather than sweeping every plan under `{plans_dir}`;
committed stale plans untouched by the session get no gate and no refusal.

### Task 5: review-plan integration point and host-limitation probe

Files:
- `agents/skills/review-plan/SKILL.md`
- `agents/hooks/plan-readiness/README.md` *(new)*
- `scripts/hooks_probe.py`

- [x] Add an Integration Points entry in `agents/skills/review-plan/SKILL.md`
  stating that its review artifacts and sidecars feed the readiness validator
  (`scripts/plan_readiness.py`) that the execute-plan and done gates call;
  verify the claim against the actual readiness conditions from Task 1 before
  wording it
- [x] Create `agents/hooks/plan-readiness/README.md` documenting: the desired
  blocking final-response enforcement; that the current Codex host cannot block
  the final response (no such hook event today); that execution
  (`execute-plan`) and finalization (`done`) gates carry enforcement until a
  host event exists; and the wiring recipe to add when one becomes available
- [x] Add a `plan-readiness` capability row to `scripts/hooks_probe.py` (same
  `(agent, hook)` matrix pattern) that reports the current per-agent state from
  the README wiring section; the expected tier is UNSUPPORTED for EVERY agent
  row today because no adapter is wired by scope; hosts differ: Claude Code
  exposes a blocking Stop-adjacent event, Codex has no blocking
  final-response event today. The
  probe must never PASS while unwired; when a host event becomes available,
  the wiring recipe is the trigger for flipping that agent's tier to a wired
  expectation, so a frozen false-UNSUPPORTED cannot hide a working adapter. Add
  the row
  for the SAME agent set as the existing `skill-gate` rows; no
  `_ADAPTER_SYMLINKS` entry is added for plan-readiness (there is no adapter to
  link), so the probe path must not consult that dict for this row. The current
  `_probe_one` checks the adapter symlink and returns FAIL on a missing or
  dangling symlink BEFORE its expected-tier early return (and would raise
  `KeyError` on the missing `_ADAPTER_SYMLINKS` lookup even earlier), so an
  UNSUPPORTED capability with no adapter can never report UNSUPPORTED; extend
  `_probe_one` to resolve an expected UNSUPPORTED tier BEFORE any
  adapter-symlink dict lookup or existence check, and pin that ordering with a
  discriminating selftest fixture:
  - [x] `hooks_probe selftest#unsupported_without_symlink`; given expected tier
    UNSUPPORTED and no adapter symlink on disk, expects the probe result
    UNSUPPORTED (not FAIL), so `--all` exits 0 while the limitation stays
    recorded
- [x] Update the `hooks_probe.py` frozen selftest pins together: the
  `len(PROBE_MATRIX) == 8` literal AND the `frozen_agents_listed` check label
  that names the cell count, so `python3 scripts/hooks_probe.py --selftest`
  stays green (an unpinned matrix-length selftest would fail on the first run
  after this task)
- [x] Run → expect GREEN: `python3 scripts/hooks_probe.py --selftest` exits 0
  and the `python3 scripts/hooks_probe.py --all` table contains a
  `plan-readiness` row reporting UNSUPPORTED (the `--all` process exit code is
  host-dependent because of pre-existing unrelated FAIL rows and is not gated)
- [x] Commit: `feat: plan-readiness host probe row and Codex final-response limitation doc`

Adjudication note (review r3, W7): the `_probe_one` early return for an
expected UNSUPPORTED tier is by design and stays; detecting a wired-but-
unflipped adapter is process discipline carried by the wiring recipe's
mandatory row-flip step (documented in `agents/hooks/plan-readiness/README.md`
and the `PROBE_MATRIX` invariant comment), not a probe property.

### Task 6: final validation and pin audit

Files:
- none new (validation only)

- [x] Mechanical pin-vs-prescription audit: extract every pinned span from the
  Validation Commands greps and verify each occurs exactly once in the
  corresponding task's prescribed text in this plan, matching with line-wrap
  tolerance (flatten newlines to single spaces and collapse whitespace runs in
  BOTH the span and the plan text before matching, because prescribed quotes
  wrap mid-span in Markdown); fix both sides of any mismatch in the same edit
- [x] Run the full Validation Commands block → expect the closing
  `ALL VALIDATION COMMANDS PASSED` line
- [x] Commit: `test: reviewed-plan readiness gate validation pass`

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-03-plan-readiness-same-n-tie-break-fixture.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-deploy-plan-readiness-runtime-copy.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-04-plan-readiness-sidecar-verdict-field.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-plan-readiness-readme-eligibility-positivity-clause.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-plan-readiness-selftest-fixture-runner-extraction.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-plan-readiness-task5-fence-annotation.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-plan-readiness-selftest-write-clean-state-privacy-rename.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-06-plan-readiness-verdict-token-comment-eligibility-wording.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-09-plan-readiness-deduplicate-date-guards.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-09-plan-readiness-scope-category-label-grammar.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-13-plan-readiness-path-shape-suffix-and-markup-tails.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-13-plan-readiness-solo-witness-gaps.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-08-31-reviewed-plan-readiness-gate.md: disposition folded into 2026-09-03-reviewed-plan-readiness-gate.md (2026-09-25); per-item file deleted.
