# Plan: Review panel hermeticity dimension

Promoted from backlog: `docs/history/backlog/2026-08-16-review-panel-hermeticity-dimension.md`
(move that file to `docs/history/backlog/completed/` when this plan completes).

Plan review: `docs/reviews/2026-08-16-plan-review-review-panel-hermeticity-dimension-r6.md` (latest, ready; r1–r5 superseded by folds and the em-dash sweep digest refresh)

## Terms

- **Ambient input**: anything a test inherits from the runner's environment instead of controlling
  it: env vars, network reachability, cwd-relative or gitignored files, clock/timezone/locale.
- **Hermetic test**: a test whose only inputs are ones it pins (fixture), patches (seam), or has
  injected (parameter); it behaves identically on any machine.
- **Review panel / worker**: the sub-agent set an orchestrator (`review-plan`,
  `doing-code-review`) launches per `review-agents/review-panel-selection.md`.
- **Lens**: a pattern catalog file in `review-agents/` (for example `testing.md`) that a worker loads.
- **Canary fixture**: a deliberately violating plan document planted in `docs/tmp/` to prove the
  panel catches the class (backlog change 5).
- **Generalize pass**: invoking the `generalize` skill to map one fixed incident to its root-cause
  principle family, so sibling defects are caught too.
- **Runtime registry**: `~/.agents/skills/`, the physical copy agents load at runtime; the repo's
  `agents/skills/` is the source of truth and must stay byte-identical for changed files.

## Gist & Examples

Review panels today can repeatedly approve test suites that are environment-dependent: the tests
inherit ambient inputs from the developer's machine, so "suite green in the review environment"
gets mistaken for "tests are hermetic". Observed shape (2026-08-16 case study, anonymized): tests
calling an orchestration entry point inherited a shell-exported API-key env var, causing live
third-party API fetches plus reads of a gitignored personal registry, roughly 9 seconds per test,
invisible across five review rounds because the reviewing agent's shell lacked the variable.

Root causes: no worker owns the hermeticity question; guards and reviews only ever run in the
review environment where the offending branch does not execute; fixes address the instance (that
path, that env var) without a generalize pass; and diff-scoped review never re-audits an old
ambient-input gate against new tests that drive it.

This plan makes the review process catch the class, in four edits plus wiring plus an acceptance
canary:

1. `severity-calibration.md` gains a category row: environment-dependent tests default **Medium**,
   promoted to **High** when the reachable input can hit paid/live APIs or read personal data.
2. `testing.md` gains a **Test Hermeticity (ambient inputs)** section: enumerate env-var reads,
   network clients, cwd-relative/gitignored paths, and clock/TZ/locale reachable from the code
   under test; verify each is pinned, patched, or injected and name the mechanism; flag any test
   driving `main`/CLI without explicit environment pinning. New pattern `testing#hermeticity-gap`.
3. `quality.md` and `documentation.md` gain one-line cross-check pointers so adjacent workers can
   raise the shape; `testing` stays the dedup lead per tiered ownership.
4. `receiving-code-review` gains a **Generalize-on-fix** step (after an accepted finding's fix
   lands, prompt a `generalize` pass), and `review-loop` references it in its iteration table.

Example of what changes for a reviewer: today a plan task saying
`CliTest#test_main_writes_report`; given `main()` invoked from the test process, expects the
report file (with the entry point reading `os.environ["..._API_KEY"]`) passes the testing
worker (coverage and assertions look fine). After this plan, the worker enumerates the env-var
read reachable from `main()`, sees no pin/patch/injection named, and stages
`testing#hermeticity-gap` at Medium minimum, blocking when the client behind the key is live.

Acceptance is behavioral, not textual: a canary fixture (a small, otherwise well-formed plan whose
single planted defect is an unpinned env-var read behind a network client) must be flagged
Medium+ with the ambient input named by a fresh five-worker `review-plan` panel. A pre-edit probe
of the same fixture against the current `testing.md` charter must produce **no** hermeticity
finding, proving the fixture is not trivially caught and the charter gap is real (the RED side
of the cycle; the fresh panel run after the edits is GREEN).

Edge cases that motivated decisions: the canary must run where the planted env var is unset and
no network is touched, mirroring root cause 2 (a runtime guard proves nothing in an environment
where the offending branch never executes); the fixture must be structurally valid so unrelated
findings do not drown the signal; wording must stay project-agnostic (no tax-repo specifics, no
real env var names) because this repo's skills are public.

## Evaluation Criteria

**Quality dimensions:**

- Class coverage (correctness of the charter): the enumeration explicitly covers the four ambient
  input families (env vars, network clients, cwd-relative/gitignored paths, clock/TZ/locale),
  each verified by a dedicated grep in Validation Commands.
- Process fidelity (primary success criterion): a fresh full-panel `review-plan` run on the canary
  fixture stages a Medium+ **blocking** finding that names the ambient input (the reachable client
  is live-capable, so the new calibration makes it blocking).
- Maintainability / single source: the enumeration procedure lives only in `testing.md`;
  `review-panel-selection.md` remains the only panel-policy source; `review-plan` carries a
  pointer mention and the sibling lenses (`quality`, `documentation`) carry cross-check pointers;
  `doing-code-review` needs no edit because its charter flows from `review-panel-selection.md`
  (forbidden-match greps in Validation Commands keep the enumeration out of orchestrators).
- Corpus hygiene: no personal paths, real env var names, or project specifics in committed skill
  files; the public hygiene scan exits 0.
- Consistency: severity stays four-tier with `blocking` independent; tiered ownership unchanged
  (testing leads hermeticity dedup).

**Done when:**

- The Validation Commands block exits 0 end-to-end, including the repo↔runtime `cmp` sync checks
  and the canary-artifact checks.
- The newest canary review artifact (`docs/reviews/*-plan-review-hermeticity-canary-r<N>.md`,
  whichever round is latest) records a Medium+ blocking hermeticity finding naming
  `CANARY_DEMO_API_KEY`.
- The backlog file has been moved to `docs/history/backlog/completed/`.

**Ship when:**

- A retro check against the case-study tax-reporting repo's review artifacts (its
  `docs/history/plans/2026-08-16-test-hermeticity-guards.md` write-up plus r1–r4 review artifacts)
  confirms the new enumeration questions would have caught the incident at plan-review time. That
  repo is external and its path is not pinned here, so this is a human-owned verification for when
  the repo is accessible; not an executable task (fail-closed classification; user-confirmed).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill files are this repo's product):**

- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/SKILL.md`
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/receiving-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `docs/history/backlog/2026-08-16-review-panel-hermeticity-dimension.md` *(move to `completed/`)*

**Tests (this repo has no test framework; the canary is the test analogue):**

- `docs/tmp/hermeticity-canary-plan.md` *(new; ephemeral fixture, gitignored)*
- `docs/reviews/<date>-plan-review-hermeticity-canary-r<N>.md` *(new; canary evidence, gitignored)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a
finding as in scope when it is **causally related to this plan**: it implements or completes a
plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an
explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is
weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** the skill files above are the documentation surface. A doc-closure sweep must
additionally grep for stale references (for example anything that describes the testing lens as
coverage-only) rather than relying on the pre-listed paths alone. `README.md` needs no change: it
contains no `review-agents` references and no catalog names or paths change.

**Out of scope; reject unless plan-related:**

- `~/.agents/skills/**` runtime copies; sync target only, kept byte-identical by Validation
  Commands group G; findings belong on the repo copy.
- The external tax-reporting repo and its plan/review artifacts; Ship-when retro check.
- Untouched `review-agents` lenses: `architecture.md`, `simplification.md`, `implementation.md`,
  `security.md`, `concurrency.md`, `premortem.md`.
- `agents/hooks/**`; the skill-gate is unrelated to this change.
- `README.md`; no catalog or path changes.

## Design Invariants (CR Guard)

- **Severity model unchanged in shape**: four tiers, `blocking` set independently. The hermeticity
  row is an addition to the category-defaults table plus a note; it must not renumber or reorder
  the decision procedures.
- **Tiered ownership preserved**: hermeticity findings lead with the `testing` worker
  (`testing#hermeticity-gap`); `quality`/`documentation` pointers must say testing leads the dedup,
  not re-home the finding.
- **Single source of truth**: the enumeration procedure exists only in `testing.md`;
  `review-panel-selection.md` remains the only panel-policy source (its testing "Owns" cell gains a
  hermeticity mention, nothing more). Only `review-plan` gains a pointer mention (worker-bundle
  row); `doing-code-review` is intentionally untouched because its panel charter flows from
  `review-panel-selection.md`, which Task 2 updates; no orchestrator may inline the enumeration
  (forbidden-match greps enforce this).
- **Public hygiene**: no personal paths, org domains, real env var names, or tax-repo specifics in
  committed skill files; the fictional `CANARY_DEMO_API_KEY` appears only in this plan's appendix
  and in gitignored tmp/reviews artifacts, never in committed skill files.
- **Repo is source of truth for skills**: `~/.agents/skills/` mirrors changed files byte-for-byte
  (sync direction repo → runtime; no deletions expected).
- **Generalize hook is a pointer**: the step references the `generalize` skill; it must not
  re-implement principle-family extraction inline.
- **Tool-agnostic wording**: new skill text must not name specific agent tools or agents
  (repo Skill Design Guidelines).

## Validation Commands

Run the whole block as a single bash invocation (it is the canonical executable artifact; every
check aborts explicitly via `fail()` (including on grep's exit 2 for missing files), so no
obligation can pass by accident). Group F is a forbidden-match sweep and must stay green by
finding nothing. Group G requires Task 6's sync; group H requires Task 6's canary run; group I
requires Task 7's backlog move; run those tasks first.

```bash
set -u
REPO="$(git rev-parse --show-toplevel)"
RA="$REPO/agents/skills/review-agents"
fail() { echo "FAIL: $1"; exit 1; }

# A. Hermeticity charter obligations in testing.md: one dedicated grep per obligation
grep -q '^## Test Hermeticity' "$RA/testing.md" || fail "A1 hermeticity section heading missing"
grep -qiE 'getenv|os\.environ|environ\[|environ\.get' "$RA/testing.md" || fail "A2 env-var enumeration missing"
grep -qiE 'urlopen|requests|httpx|socket' "$RA/testing.md" || fail "A3 network-client enumeration missing"
grep -qiE 'cwd-relative|gitignored' "$RA/testing.md" || fail "A4 filesystem enumeration missing"
grep -qiE 'clock|timezone|locale' "$RA/testing.md" || fail "A5 clock/TZ/locale enumeration missing"
grep -qiE 'pinned|patched|injected' "$RA/testing.md" || fail "A6 pin/patch/inject verification missing"
grep -q 'testing#hermeticity-gap' "$RA/testing.md" || fail "A7 pattern id missing"

# B. Severity calibration row with Medium floor, plus the blocking note (dedicated greps)
grep -qi 'Environment-dependent test' "$RA/severity-calibration.md" || fail "B1 severity row missing"
grep -i -A2 'Environment-dependent test' "$RA/severity-calibration.md" | grep -q 'Medium' || fail "B2 Medium default missing"
grep -i 'Environment-dependent tests' "$RA/severity-calibration.md" | grep -qi 'blocking' || fail "B3 blocking note missing (same-line conjunction per Task 1 note obligation)"

# C. Charter wiring: panel selection, lens index, review-plan bundle (pointer mentions)
grep -qi 'hermeticity' "$RA/review-panel-selection.md" || fail "C1 testing Owns cell missing hermeticity"
grep -i 'hermeticity' "$RA/SKILL.md" | grep -q 'testing' || fail "C2 lens index row missing hermeticity"
grep -i 'hermeticity' "$REPO/agents/skills/review-plan/SKILL.md" | grep -qi 'testing' || fail "C3 worker bundle row missing hermeticity"

# D. Adjacent-worker pointers
grep -qi 'hermeticity' "$RA/quality.md" || fail "D1 quality pointer missing"
grep -qi 'hermeticity' "$RA/documentation.md" || fail "D2 documentation pointer missing"

# E. Generalize-on-fix hook in both skills
grep -qi 'generalize-on-fix' "$REPO/agents/skills/receiving-code-review/SKILL.md" || fail "E1 receiving-code-review step missing"
grep -qi 'generalize-on-fix' "$REPO/agents/skills/review-loop/SKILL.md" || fail "E2 review-loop reference missing"

# F. Single source: enumeration details must NOT leak into orchestrators/panel policy (expect zero matches)
# F0 existence pre-check first: grep exits 2 on a missing file, which an inverted if-condition
# would silently read as "no forbidden match"; a wrong path must abort, not pass.
for p in "$REPO/agents/skills/review-plan/SKILL.md" \
         "$REPO/agents/skills/doing-code-review/SKILL.md" \
         "$RA/review-panel-selection.md"; do
  test -f "$p" || fail "F0 missing file: $p"
done
if grep -qiE 'getenv|urlopen|httpx' \
     "$REPO/agents/skills/review-plan/SKILL.md" \
     "$REPO/agents/skills/doing-code-review/SKILL.md" \
     "$RA/review-panel-selection.md"; then
  fail "F1 enumeration leaked outside testing.md"
fi

# G. Repo ↔ runtime registry byte-identical for every changed file
for f in testing.md severity-calibration.md quality.md documentation.md review-panel-selection.md SKILL.md; do
  cmp -s "$RA/$f" "$HOME/.agents/skills/review-agents/$f" || fail "G review-agents/$f diverged from runtime registry"
done
cmp -s "$REPO/agents/skills/receiving-code-review/SKILL.md" "$HOME/.agents/skills/receiving-code-review/SKILL.md" || fail "G receiving-code-review diverged"
cmp -s "$REPO/agents/skills/review-loop/SKILL.md" "$HOME/.agents/skills/review-loop/SKILL.md" || fail "G review-loop diverged"
cmp -s "$REPO/agents/skills/review-plan/SKILL.md" "$HOME/.agents/skills/review-plan/SKILL.md" || fail "G review-plan diverged"

# H. Canary evidence: the newest canary artifact records a Medium+ BLOCKING hermeticity finding
# naming the ambient input. H1 selects the artifact with the HIGHEST round suffix (r<N>), not the
# newest mtime: Task 6's recovery path re-runs with r2+ and review-plan names artifacts by run
# date, and a later edit to an older round must not make a stale artifact win. Parsing arbitrary
# staging prose is fragile: severity, pattern, and blocking live on separate field lines, and
# section granularity varies by artifact, so Task 6 records a dedicated evidence line under a
# "### Canary evidence" heading, quoting the staged finding verbatim. H3 matches that line's
# FIXED field order (input, then severity, then blocking; authoring rule 9). H2 greps the
# pattern id INSIDE the ## Findings section only, excluding the Overflow-manifest and
# Soften-watchlist subsections (they may cite the pattern without a staged finding), so a
# fabricated evidence line without a real finding fails H2.
CANARY="$(ls -1 "$REPO"/docs/reviews/*plan-review-hermeticity-canary-r*.md 2>/dev/null | sed 's/.*-r\([0-9][0-9]*\)\.md$/\1 &/' | sort -n | tail -n 1 | cut -d' ' -f2-)"
[ -n "$CANARY" ] && [ -f "$CANARY" ] || fail "H1 no canary artifact found (docs/reviews/*plan-review-hermeticity-canary-r*.md)"
awk '/^## Findings/{f=1; next} /^## /{f=0} /^### (Overflow|Soften)/{f=0} f' "$CANARY" | grep -q 'testing#hermeticity-gap' \
  || fail "H2 canary ## Findings section does not use pattern testing#hermeticity-gap"
grep -qE 'CANARY-EVIDENCE: input=CANARY_DEMO_API_KEY severity=(Medium|High|Critical) blocking=true' "$CANARY" \
  || fail "H3 canary evidence line missing or below acceptance (input named + Medium+ + blocking=true)"

# I. Hygiene + backlog completion. I1 runs the hygiene scan ANCHORED to the repo root in a
# subshell: the script resolves its scan root from the invocation cwd and silently PASSes
# (exit 0, scanning nothing) when launched from elsewhere, the same environment-dependent
# silent-pass class this plan targets.
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh ) || fail "I1 public hygiene scan failed"
BACKLOG="$REPO/docs/history/backlog/2026-08-16-review-panel-hermeticity-dimension.md"
if [ -e "$BACKLOG" ] || [ ! -f "$REPO/docs/history/backlog/completed/2026-08-16-review-panel-hermeticity-dimension.md" ]; then
  fail "I2 backlog file not moved to completed/"
fi
echo "ALL CHECKS PASSED"
```

Negative-path self-check (authoring rule 10): stripping any single A–E obligation makes its grep
exit non-zero and `fail` aborts (grep exit 2 on missing files aborts too); a wrong F-listed path
trips F0; adding a `getenv` enumeration line to any F-listed file trips F1; an unsynced runtime
copy trips G; a canary run whose `## Findings` section never uses `testing#hermeticity-gap`
trips H2; an evidence line with `severity=Low`, `blocking=false`, a swapped field order, or a
missing input name trips H3 (fixed-order single-line match per authoring rule 9); running the
hygiene scan from a directory other than the repo root trips I1's anchoring.

### Task 1: Severity floor for environment-dependent tests

Files:
- `agents/skills/review-agents/severity-calibration.md`

- [x] In the **Category defaults** table, add one row: finding type `Environment-dependent test`
  (a test that can inherit an unpinned ambient input reachable from the code under test);
  Default `Medium`; Promote to Medium when `(default is already Medium)`; Promote to High/Critical
  when `the reachable input can hit paid/live APIs or read gitignored personal data → High`.
- [x] Below the table, add one short note tying the row to the blocking procedure: an
  environment-dependent test whose reachable input can hit paid/live APIs or read personal data is
  `blocking: true` (running the suite creates concrete side-effect/privacy risk, and a green run
  in a clean environment verifies nothing; the same logic as an unverifiable change). Write the
  note as prose whose **first line contains both the phrase `Environment-dependent tests` and the
  word `blocking`** (Validation B3 greps that same-line conjunction); do not renumber or reorder
  the existing decision procedures.
- [x] Commit: `review-agents: severity default for environment-dependent tests`

### Task 2: Testing-worker hermeticity charter (RED probe, then GREEN edits)

Files:
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/SKILL.md`
- `docs/tmp/hermeticity-canary-plan.md` *(new; gitignored)*

- [x] Create the canary fixture at `docs/tmp/hermeticity-canary-plan.md` with exactly the content
  from the **Canary fixture** appendix below (a small, structurally valid plan whose single
  planted defect is a test driving `main()` with an unpinned `CANARY_DEMO_API_KEY` env read
  behind a live client and a cwd-relative output path).
- [x] RED probe: reason the fixture through the **current** `testing.md` charter (inline; no panel
  launch needed) and record in the task log that it produces no hermeticity finding, proving the
  fixture is not trivially flagged and the charter gap is real. If the current charter would
  already flag it, strengthen the fixture's disguise (keep the defect) rather than weakening the
  new section later.
- [x] Add a `## Test Hermeticity (ambient inputs)` section to `testing.md` covering, for every
  new/changed test (code review) or test-bearing plan task (plan review): (1) enumerate ambient
  inputs reachable from the code under test: env-var reads (`getenv`/`environ`) over the call
  graph the test drives, network clients (`urlopen`, `requests`, `httpx`, socket use),
  cwd-relative and gitignored/uncommitted paths, clock/timezone/locale dependence; (2) verify each
  is pinned (fixture), patched (seam), or injected (parameter), and name the mechanism in the
  review output; (3) flag any test driving an orchestration entry point (`main`, CLI) without
  explicit environment pinning; a suite green only where the gating env var is absent proves
  nothing. Pattern `testing#hermeticity-gap`; default severity per the
  `severity-calibration.md` row from Task 1; reachable paid/live API or personal-data cases are
  blocking. Keep wording project- and tool-agnostic.
- [x] In `review-panel-selection.md`, extend only the testing worker's **Owns** cell in the
  five-worker table to end with `, test hermeticity (ambient-input enumeration)`; no other panel
  policy changes.
- [x] In `review-agents/SKILL.md`, update the lens index row for `testing.md` to include
  `hermeticity (ambient inputs)`.
- [x] Commit: `review-agents: testing-worker hermeticity charter`

### Task 3: Adjacent-worker cross-check pointers

Files:
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/documentation.md`

- [x] In `quality.md`, add a short `## Hermeticity cross-check` block: when tracing call graphs
  or data flows, note ambient-input reads (env vars, network clients, cwd-relative/gitignored
  paths, clock/TZ/locale) reachable from tests in the diff or plan; raise with a `quality#`
  prefix when visible; the `testing` worker leads the dedup group per `review-panel-selection.md`
  (enumeration procedure lives in `testing.md`).
- [x] In `documentation.md` phase 1, extend the **Plan / RFC prose (phase 1)** section (currently
  a single prose sentence) with one added item, converting the sentence to a bullet or appending
  alongside it: flag plan test tasks that drive orchestration entry points (`main`, CLI) without
  environment pinning, citing the `testing.md` hermeticity enumeration; `testing` leads the dedup.
- [x] Commit: `review-agents: hermeticity cross-check pointers in quality and documentation lenses`

### Task 4: Generalize-on-fix hook

Files:
- `agents/skills/receiving-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [x] In `receiving-code-review/SKILL.md`, add a short `## Generalize-on-fix` section after
  **Agent corpus feedback**: after a finding is accepted AND its fix lands (staging triage or
  ad-hoc partner feedback), prompt a `generalize` pass on the incident: map the instance fix to
  its root-cause principle family and propose the smallest corpus/catalog update; narrow instance
  fixes (that path, that glob) let sibling defects survive later rounds. Cross-reference Agent
  corpus feedback (findings the panel missed) as the sibling rule; do not duplicate its steps.
- [x] In `review-loop/SKILL.md`, extend the step 3 row of the **One iteration** table with:
  after fixes land, run the **Generalize-on-fix** step from `receiving-code-review`. One line
  only: reference, no restatement.
- [x] Commit: `skills: generalize-on-fix hook in review triage and loop`

### Task 5: review-plan worker-bundle wiring

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] In the **Worker bundles** table, extend the `testing` row's focus to include
  `hermeticity of proposed tests (ambient-input enumeration per testing.md)`. Pointer mention
  only; the enumeration must stay in `testing.md` (forbidden-match grep F1 enforces).
- [x] Commit: `review-plan: hermeticity in testing worker bundle`

### Task 6: Sync runtime registry, then canary GREEN (fresh panel)

Files:
- `~/.agents/skills/review-agents/{testing,severity-calibration,quality,documentation,review-panel-selection,SKILL}.md` *(runtime copies)*
- `~/.agents/skills/receiving-code-review/SKILL.md`, `~/.agents/skills/review-loop/SKILL.md`, `~/.agents/skills/review-plan/SKILL.md` *(runtime copies)*
- `docs/reviews/<run-date>-plan-review-hermeticity-canary-r<N>.md` *(new; gitignored)*

- [x] Diff repo vs runtime registry for the nine changed files (bidirectional-sync discipline:
  identify additions/updates/deletions explicitly; expect updates only, no deletions), then copy
  each changed file repo → `~/.agents/skills/` so the canary panel loads the updated catalogs.
- [x] GREEN canary: launch a fresh `review-plan` run (full five-worker panel per its skill) on
  `docs/tmp/hermeticity-canary-plan.md`, with `CANARY_DEMO_API_KEY` unset in the launching
  environment; the run writes its artifact to
  `docs/reviews/<run-date>-plan-review-hermeticity-canary-r<N>.md` following `review-staging`
  (r1 expected first; Validation group H reads the newest matching artifact, so later rounds are
  covered). The fixture intentionally lives in `{tmp_dir}` rather than `{plans_dir}`: it is not a
  real plan, must not be archived on completion, and its path is passed explicitly to the run.
  Given the planted fixture and the updated charters, expects at least one staged finding at
  Medium or higher from the testing worker that names the ambient input `CANARY_DEMO_API_KEY`
  with pattern `testing#hermeticity-gap`; per the Task 1 calibration it is blocking.
- [x] Record the canary evidence in the same artifact under a `### Canary evidence` heading as
  one line quoting the real staged finding (do not fabricate values; Validation H2 independently
  requires the pattern id in the finding body):
  `CANARY-EVIDENCE: input=CANARY_DEMO_API_KEY severity=<Medium|High|Critical> blocking=true finding=F<N>`
  The exact field order is `input`, `severity`, `blocking` (Validation H3 matches the ordered line).
- [x] If the panel does not flag it: fix the charter wording (make the enumeration louder or the
  entry-point rule more explicit in `testing.md`), not just the fixture, re-sync, and re-run as
  the next `-r<N>`; do not weaken severity or delete the acceptance.
- [x] No repo files change in this task unless the previous checkbox forced a wording fix (then
  commit that fix as `review-agents: sharpen hermeticity charter after canary r<N>`); the canary
  artifact itself is gitignored and syncs to the `docs` shadow branch via `done`/`docs-branch`.

### Task 7: Final validation sweep and backlog completion

Files:
- `docs/history/backlog/2026-08-16-review-panel-hermeticity-dimension.md` *(move to `docs/history/backlog/completed/`)*

- [x] Run the full **Validation Commands** block as one bash invocation; require
  `ALL CHECKS PASSED` (groups A–I; negative-path self-check per the note under the block).
- [x] Doc-closure sweep: list every surface that describes the testing lens
  (`rg -i -l "testing\\.md" agents/ README.md`) and confirm each hit either already mentions
  hermeticity or is out of scope (record the one-line classification per hit; update any stale
  description alongside its source copy). A plain text grep cannot prove absence of omission, so
  the recorded per-hit classification is the evidence, not the empty result alone.
- [x] Create the completion directory if absent (`mkdir -p docs/history/backlog/completed/`;
  `git mv` requires an existing destination), then move the backlog file there (its own
  documented workflow).
- [x] Commit: `docs: complete review-panel hermeticity backlog (canary green)`

## Canary fixture (appendix; exact content for `docs/tmp/hermeticity-canary-plan.md`)

Structurally valid on purpose: every section `review-plan` expects is present and every test item
uses the given/expects format, so the hermeticity violation is the dominant signal. The env var
name is fictional. Do not set `CANARY_DEMO_API_KEY` in any shell that touches this fixture.

````markdown
# Plan: Demo report batch runner

## Gist & Examples

Add a small batch runner that fetches demo exchange rates and writes the monthly report file.
Greenfield: both files below are new.

## Evaluation Criteria

**Quality dimensions:**
- correctness: report file reflects fetched rates

**Done when:**
- `python -m pytest tests/test_demo_cli.py` passes
- `out/report.csv` exists after the run

**Ship when:**
- partner review of the generated report

## Review Scope

**Explicit must-fix:**
- `src/demo_reporting/cli.py` *(new)*
- `tests/test_demo_cli.py` *(new)*

**Plan-related extension:** standard two-tier rule.

**Out of scope; reject unless plan-related:**
- `src/demo_reporting/rates.py`; pre-existing library, only imported

## Validation Commands

```bash
python -m pytest tests/test_demo_cli.py
```

### Task 1: CLI entry point and test

Files:
- `src/demo_reporting/cli.py` *(new)*
- `tests/test_demo_cli.py` *(new)*

Entry point to implement:

```python
# src/demo_reporting/cli.py
import os
from demo_reporting.rates import fetch_rates

def main() -> int:
    api_key = os.environ["CANARY_DEMO_API_KEY"]
    rates = fetch_rates(api_key)
    with open("out/report.csv", "w") as fh:
        fh.write(format_report(rates))
    return 0
```

- [ ] `DemoCliTest#test_main_writes_report`; given `main()` invoked from the test process, expects `out/report.csv` created with the fetched rates
- [ ] Run → expect RED: `python -m pytest tests/test_demo_cli.py`
- [ ] Write minimal implementation
- [ ] Run → expect GREEN
- [ ] Commit: `feat: demo report batch runner`
````
