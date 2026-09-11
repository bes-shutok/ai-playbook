# Plan: Grilling-family local fork visibility

Backlog origin (scope of record): `docs/history/backlog/2026-09-09-grilling-fork-answer-state-rules.md`. Prior-phase context: `docs/plans/completed/2026-09-08-plans-grill-answer-state-machine.md` (its Task 6 recorded this backlog item; that plan introduced the fork rules this plan makes visible).

Reviews for THIS plan live under the prefix `docs/reviews/2026-09-09-plan-review-grilling-fork-answer-state-rules-r1.md`, `-r2.md`, and so on for each later round.

## Terms

- **Local fork**: deliberate, maintained divergence of a vendored skill in this repository from its upstream source (the `metadata.upstream` value in its SKILL.md frontmatter).
- **Upstream sync**: applying upstream changes into `agents/skills/<name>/` under the repo's Vendored Asset Sync Rules, with `rsync --delete` semantics; in a naive run, unlisted files and pre-existing file content do not survive.
- **Answer-state rule family**: the fork's interview contract rules: per-question `open`/`closed` answer state, the exact opt-in phrase "accept the recommendation for this question", per-question decision receipts, the question-economy and consolidated-assumptions-list rule, and the generic-acknowledgement and lifecycle-verb rules.
- **Fork notice**: the visible blockquote divergence inventory inserted after the H1 heading of each forked SKILL.md, plus its `metadata.local_fork` frontmatter key.

## Assumptions

- assume the fork rule text in both files stays byte-identical; this plan only adds provenance and sync-protection markers; basis: the backlog item asks for visibility only, and the origin plan's Task 6 design invariant records the fork as deliberate.
- assume the divergence inventory in the Task 1 and Task 2 notices is accurate; basis: upstream sources fetched 2026-09-09 from raw.githubusercontent.com (mattpocock/skills main: `productivity/grilling` 28 lines, `engineering/grill-with-docs` 7 lines) and diffed against the working tree: local grilling replaces the upstream frontier/rounds cadence with the three-phase default cadence and adds batch-all mode, self-contained question rules, the mandatory ambiguity triggers, the lifecycle-verb clarification trigger, the no-generic-acknowledgement rule, the answer-state rule family, and the Integration Points section with its plans sync note; local grill-with-docs expands the one-line upstream body into the Workflow with inline domain-modeling application, restates the answer-state family in Workflow step 2, adds its own Integration Points section, and deliberately omits upstream's `disable-model-invocation: true` frontmatter flag.
- assume the sync-rule home is the existing `## Vendored Asset Sync Rules` section of the repository `AGENTS.md`, not a new registry file; basis: standing pre-authorization on the authoring task (2026-09-09) accepts the recommended option; AGENTS.md already owns sync policy and sits outside the vendored directories an upstream sync overwrites.
- assume the in-file marker form is a frontmatter `local_fork` key plus the visible Fork notice blockquote in each file; basis: same standing pre-authorization; the frontmatter key is machine-greppable, the blockquote is human- and agent-visible at the top of the file.
- assume git history of the two skill paths is the re-application source of record after a sync wipe; basis: the repository tracks the forked files and the fork rules landed in the origin plan's commits.
- assume no README.md catalog change is needed; basis: skill names, paths, and usage do not change, and the repo guideline ties README updates to exactly those.

Decision points requiring a grill: none remain.

## Gist & Examples

Two vendored skills (`agents/skills/grilling/`, `agents/skills/grill-with-docs/`) carry a deliberate local fork: the entire local interview cadence, the answer-state rule family, the Integration Points sections, and (for grill-with-docs) the deliberate removal of upstream's `disable-model-invocation` flag. Today that fork is invisible to the one operation that can destroy it: an upstream sync.

**Before (today):** an operator syncs upstream into `agents/skills/grilling/` with `rsync --delete` semantics. SKILL.md is replaced wholesale; the answer-state rule, the opt-in phrase, the receipts rule, the question-economy rule, the cadence rewrite, and the integration points disappear. Nothing in the repository records that the directory carried deliberate divergence: no marker on the file, no sync rule naming the skill, no check that fails. The loss is silent, and the next plan or interview silently loses the answer-state contract.

**After (this plan):** the same sync runs, but each SKILL.md now opens with a Fork notice naming every deliberate divergence, and its frontmatter carries a `local_fork` key. The repository AGENTS.md Vendored Asset Sync Rules name both skills as fork carriers and require the sync to re-apply the fork from git history of these paths or consciously drop it with the decision recorded. If a syncer ignores both layers anyway, the plan's validation greps (notice pins plus fork-sentence pins) fail loudly instead of staying green. Edge case that motivated an explicit line in the grill-with-docs notice: upstream carries `disable-model-invocation: true` and this fork deliberately omits it, so a well-meaning "repair" during a sync must not restore it; the notice says so and a negative validation pin enforces it.

## Evaluation Criteria

**Quality dimensions:**
- visibility: each forked file carries both layers (frontmatter `local_fork` key and visible Fork notice), and AGENTS.md carries the sync rule; each layer mechanically greppable
- correctness: every validation pin is unique in its target file (verified at authoring on 2026-09-09) and the full Validation Commands block exits 0 after Tasks 1 through 3
- minimality: insertions only; no fork-rule text, frontmatter `name`/`description`, or `metadata.upstream` value changes
- hygiene: em-dash scan and public-hygiene scan clean over the changed files

**Done when:**
- the complete Validation Commands block, run from the repository root after Tasks 1 through 3, prints `ALL VALIDATION CHECKS PASSED` and exits 0
- `bash scripts/check-no-em-dash.sh file` over the three changed files exits 0 (verified clean at authoring time, so the whole-file scope is satisfiable)
- `bash scripts/scan-public-hygiene.sh` from the repository root exits 0

**Ship when:** a future upstream sync of these two directories consults the AGENTS.md rule and records re-application or a conscious drop; process-owned evidence outside this repository, prose only.

## Design Invariants (CR Guard)

- The fork rule text in both SKILL.md files is frozen; only the prescribed insertions are allowed. Reject any review finding or execution step that edits the answer-state, opt-in-phrase, receipts, question-economy, cadence, trigger, or integration-point text.
- Frontmatter `name`, `description`, and the `upstream` value stay unchanged in both files.
- The absence of `disable-model-invocation` in grill-with-docs frontmatter is a deliberate fork decision and must survive; the negative validation pin enforces it.
- The Fork notice is inert provenance metadata: it must not add, remove, or modify any interview rule; agents loading the skill read it as provenance, not as a new behavior.
- Inserted text uses repository-relative references only (the skills are public; no machine-specific absolute paths, personal identifiers, or org-specific names).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/grilling/SKILL.md` (insertion only; all other content frozen)
- `agents/skills/grill-with-docs/SKILL.md` (insertion only; all other content frozen)
- `AGENTS.md` (one bullet appended inside `## Vendored Asset Sync Rules`; rest frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `README.md`; no skill name, path, or usage change
- `agents/skills/grilling/LICENSE.txt` and `agents/skills/grill-with-docs/LICENSE.txt`; licensing already in place, no new skill directory
- `agents/skills/plans/SKILL.md`; its Step 1.4 sync note changes only when the mirrored grilling clauses change, and this plan changes no clause text
- the upstream repository (mattpocock/skills); read-only diff source, never a write target
- `docs/history/backlog/2026-09-09-grilling-fork-answer-state-rules.md`; moves to `{backlog_completed_dir}` at plan completion per Plan Lifecycle, not by an execution task

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root AFTER Tasks 1-3. Every check aborts non-zero on miss.
set -u

fail() { echo "VALIDATION FAIL: $1"; exit 1; }
expect_pin() { # expect_pin <file> <fixed-string>
  grep -qF -- "$2" "$1" || fail "missing in $1: $2"
}

G=agents/skills/grilling/SKILL.md
GWD=agents/skills/grill-with-docs/SKILL.md
A=AGENTS.md
test -f "$G" || fail "missing $G"
test -f "$GWD" || fail "missing $GWD"
test -f "$A" || fail "missing $A"

# 1. Fork notice markers (RED today, GREEN after Tasks 1-2; a sync wipe breaks these).
expect_pin "$G" 'local_fork: "deliberate'
expect_pin "$G" '**Local fork notice:**'
expect_pin "$G" 'recovery source: git history of this path'
expect_pin "$GWD" 'local_fork: "deliberate'
expect_pin "$GWD" '**Local fork notice:**'
expect_pin "$GWD" 'recovery source: git history of this path'

# 2. grilling fork sentences (GREEN before and after this plan; a sync wipe breaks these).
expect_pin "$G" '**Default cadence (unclear-first sequential, clear tail batched):**'
expect_pin "$G" '**Batch-all mode (when the user asks for it):**'
expect_pin "$G" 'accept the recommendation for this question'
expect_pin "$G" 'RESUMES the interview (restate the same question or ask the next one)'
expect_pin "$G" 'an answer to a different question does not close the unanswered one'
expect_pin "$G" '**Answer state:**'
expect_pin "$G" 'record a one-line decision receipt (decision, source, date, affected plan section) before asking the next question'
expect_pin "$G" 'presented as one consolidated list at the end of the interview'
expect_pin "$G" '**Mandatory ambiguity triggers (cleanup and restoration):**'
expect_pin "$G" '**Lifecycle-verb clarification trigger:**'
expect_pin "$G" '**No generic acknowledgement confirms a material choice:**'
expect_pin "$G" 'Sync note: the plans Step 1.4 confirmation meta-rule mirrors this skill'
expect_pin "$G" '## Integration Points'

# 3. grill-with-docs fork sentences (GREEN before and after this plan; a sync wipe breaks these).
expect_pin "$GWD" 'The interview tracks each material question'
expect_pin "$GWD" 'accept the recommendation for this question'
expect_pin "$GWD" 'Do not batch glossary or ADR updates to the end of the session.'
expect_pin "$GWD" '### With `execute-plan` skill'
expect_pin "$GWD" 'record the answer as a one-line receipt (decision, source, date, affected plan section) in the requirements buffer'
expect_pin "$GWD" '## Integration Points'

# 4. The deliberate absence of disable-model-invocation in grill-with-docs FRONTMATTER must
#    survive; body mentions inside the Task 2 Fork notice are expected, so the sweep is scoped
#    to the frontmatter region only (extraction is fail-closed on the fence anchor).
GWD_FM="$(awk 'NR==1 && /^---$/{f=1;next} f && /^---$/{exit} f' "$GWD")"
test -n "$GWD_FM" || fail "cannot extract frontmatter from $GWD"
rc=0
printf '%s\n' "$GWD_FM" | grep -q "disable-model-invocation"; rc=$?
if [ "$rc" -ge 2 ]; then fail "grep error on $GWD frontmatter"; fi
if [ "$rc" -eq 0 ]; then fail "disable-model-invocation must stay absent in $GWD frontmatter (deliberate fork omission)"; fi

# 5. AGENTS.md vendored-sync rule (RED today, GREEN after Task 3; a rules revert breaks these).
expect_pin "$A" 'carry a deliberate local fork of their upstream sources'
expect_pin "$A" 'consciously drop it with the decision recorded'

# 6. Frontmatter minimality witness: names, descriptions, and upstream identity stay unchanged.
expect_pin "$G" 'name: grilling'
expect_pin "$G" 'description: Grill the user relentlessly about a plan, decision, or idea.'
expect_pin "$G" 'upstream: "https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling"'
expect_pin "$GWD" 'name: grill-with-docs'
expect_pin "$GWD" 'description: Relentless interview to sharpen a plan or design'
expect_pin "$GWD" 'upstream: "https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs"'

echo "ALL VALIDATION CHECKS PASSED"
```

### Task 1: grilling SKILL.md fork notice

Files:
- `agents/skills/grilling/SKILL.md`

- [ ] In the frontmatter `metadata` block, directly under the `upstream` line, insert exactly:
  ```yaml
    local_fork: "deliberate; see the Local fork notice below and the Vendored Asset Sync Rules in the repository AGENTS.md"
  ```
- [ ] Directly after the `# Grilling` H1 line (before the first body paragraph), insert exactly this single-line blockquote:
  ```markdown
  > **Local fork notice:** this file carries a deliberate local fork of the upstream `productivity/grilling` skill (`metadata.upstream`). Deliberate divergences: the three-phase default cadence (unclear-first sequential, clear tail batched) replaces the upstream frontier/rounds format; batch-all mode; self-contained question rules; the mandatory ambiguity triggers (cleanup and restoration); the lifecycle-verb clarification trigger; the no-generic-acknowledgement rule; the answer-state rule (per-question `open`/`closed`); the opt-in phrase "accept the recommendation for this question"; per-question decision receipts; question economy with the consolidated assumptions list; the Integration Points section and its sync note with the plans skill Step 1.4 meta-rule. A future upstream sync of this directory must re-apply this fork (recovery source: git history of this path) or consciously drop it with the decision recorded; see the Vendored Asset Sync Rules in the repository AGENTS.md.
  ```
- [ ] Verify insertion-only: `git diff --stat agents/skills/grilling/SKILL.md` shows insertions and no deletions
- [ ] Commit: `skills: mark grilling local fork in SKILL.md`

### Task 2: grill-with-docs SKILL.md fork notice

Files:
- `agents/skills/grill-with-docs/SKILL.md`

- [ ] In the frontmatter `metadata` block, directly under the `upstream` line, insert exactly:
  ```yaml
    local_fork: "deliberate; see the Local fork notice below and the Vendored Asset Sync Rules in the repository AGENTS.md"
  ```
- [ ] Directly after the `# Grill with docs` H1 line (before `Run a `grilling` session...`), insert exactly this single-line blockquote:
  ```markdown
  > **Local fork notice:** this file carries a deliberate local fork of the upstream `engineering/grill-with-docs` skill (`metadata.upstream`). Deliberate divergences: the expanded Workflow (inline `domain-modeling` application, doc-path resolution before the first question, a doc summary on confirmation); the answer-state restatement in Workflow step 2 (per-question `open`/`closed` state, the opt-in phrase "accept the recommendation for this question", per-question decision receipts, the consolidated assumptions list); the no-batching rule for glossary and ADR updates; the Integration Points section (grilling, premortem, execute-plan, rfc-design/plans); and the deliberate omission of the upstream `disable-model-invocation: true` frontmatter flag, which must NOT be restored by a sync. A future upstream sync of this directory must re-apply this fork (recovery source: git history of this path) or consciously drop it with the decision recorded; see the Vendored Asset Sync Rules in the repository AGENTS.md.
  ```
- [ ] Verify insertion-only: `git diff --stat agents/skills/grill-with-docs/SKILL.md` shows insertions and no deletions
- [ ] Commit: `skills: mark grill-with-docs local fork in SKILL.md`

### Task 3: AGENTS.md vendored-sync rule

Files:
- `AGENTS.md`

- [ ] In the `## Vendored Asset Sync Rules` section, append exactly this bullet after the last existing bullet of that section:
  ```markdown
  - `agents/skills/grilling/` and `agents/skills/grill-with-docs/` carry a deliberate local fork of their upstream sources (answer-state rule family, opt-in phrase, decision receipts, question economy, cadence rewrite, integration points; see each file's Local fork notice). An upstream sync of these directories must re-apply the fork from git history of these paths or consciously drop it with the decision recorded; never overwrite the fork silently.
  ```
- [ ] Verify insertion-only: `git diff AGENTS.md` shows one added line and no removed lines
- [ ] Commit: `docs: require re-applying the grilling-family local fork on upstream sync`

### Task 4: full validation and hygiene gate

Files: none (verification only)

- [ ] Run the complete Validation Commands block from the repository root → expect `ALL VALIDATION CHECKS PASSED`
- [ ] Run `bash scripts/check-no-em-dash.sh file agents/skills/grilling/SKILL.md agents/skills/grill-with-docs/SKILL.md AGENTS.md` → expect exit 0
- [ ] Run `bash scripts/scan-public-hygiene.sh` from the repository root → expect exit 0
- [ ] Commit any remaining unstaged plan-owned files: `plans: grilling fork visibility validation pass`
