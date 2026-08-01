# Plan: Review skills: explicit comparison basis + large-diff confirmation

Plan review: `docs/reviews/2026-08-01-plan-review-review-skills-explicit-basis-r2.md` (latest, ready) · `docs/reviews/2026-08-01-plan-review-review-skills-explicit-basis-r1.md` (r1)

## Terms

- **Basis (for comparison):** the `<base>` (branch / commit / tag) that a review diff is computed against, i.e. the `B` in `git diff <base>...<head>`. "Obvious" means it resolves unambiguously from context (PR URL → PR base; explicit `against X` arg; single open PR on the branch).
- **Magnitude threshold:** the diff byte size at which the change counts as "unexpectedly large" and the proposed basis must be confirmed before review. Key `review_large_diff_bytes`, default `10240` (10 kB), measured via `git diff <base>...<head> | wc -c`.
- **Diff-based reviewer:** a skill that reviews a git diff against a base. Only `doing-code-review` and `review-loop` qualify; the other `review-*` skills review a document or existing PR threads and have no before/after diff.

## Gist & Examples

Today both diff-based review skills resolve the comparison base **silently**:

- `doing-code-review` infers the base from the PR URL for PR reviews, and for **branch reviews** leaves `<base>` as a literal placeholder with no resolution step at all (`SKILL.md:50,62,124`).
- `review-loop` has a 3-tier silent fallback: user arg → open-PR base → repo default `main`/`master` (`SKILL.md:33-37`). Tier 3 is a guess, not a confirmation.

Neither skill checks whether the change is unexpectedly large before committing the user to a full multi-worker panel review.

This plan adds two interactive-basis rules to **both** skills:

1. **Explicit basis when not obvious.** If the base cannot be resolved unambiguously (no PR URL, no explicit `against X`, no single open PR, ambiguous integration branch), **ask the user** for the comparison base before proceeding. Do not silently fall back to a default or leave `<base>` as a placeholder.
2. **Large-diff basis confirmation.** After resolving the base, measure `git diff <base>...<head> | wc -c`. If it exceeds `review_large_diff_bytes` (default 10240), **confirm the basis with the user before launching review**; state the size and the proposed base, proceed only once confirmed.

**Examples of the new behavior:**

- *"review this branch"* (no PR, no base named) → ask: "What should I diff against?" before reviewing. *(Previously: silently used a placeholder or guessed `main`.)*
- *"review-loop"* on a branch whose diff is 47 kB with no base named → resolve base, then: "This diff is ~47 kB against `main`; confirm that's the right comparison base before I start the loop?" *(Previously: silent 3-tier fallback, no size signal.)*
- *"review this PR"* (GitHub URL) → base resolves unambiguously from the PR; if the diff is ≤ 10 kB, **no new prompt**. *(Unchanged path; the rules only trigger when the base is non-obvious or the diff is large.)*

### Design Invariants (CR Guard)

- **PR-URL mode is prompt-free when the diff is small.** The PR URL resolves `base`/`head` unambiguously; the explicit-basis rule must NOT add a prompt in that case. Rationale: the rule exists for *ambiguous* bases; an open PR's base is the definition of unambiguous.
- **Non-interactive context is prompt-free but auditable (fold of risk-F1).** When the skill is invoked as a sub-agent of an autonomous orchestrator (`execute-plan` Phase 3 branch review; `review-loop` round 1) OR in a session with no user at the console (CI/scheduled), the "ask the user" / "confirm the basis" rules must NOT emit an interactive prompt. That would violate `execute-plan`'s "no asking between steps; pause only on hard gates" contract (`execute-plan/SKILL.md:27`) and hang a headless run. Instead, resolve the base via the existing tier fallback (repo default integration branch per `AGENTS.md`) and **record the resolution + the reason in the staging-doc Metadata** (e.g. `Base resolved non-interactively: main (repo default; no PR/arg, autonomous sub-agent)`) so it is auditable rather than silent. The prompt fires only in an interactive top-level session.
- **Magnitude check is defined once; review-loop delegates (fold of design-simplicity-F1).** `review-loop` Step 1 *is* a `doing-code-review` launch (`review-loop/SKILL.md:49,164-165`). So `doing-code-review` Step 1 owns the magnitude-confirmation rule. `review-loop` Step 0 owns only **base resolution** (the tier rewrite) plus a one-sentence **large-diff guard that delegates** ("if the diff exceeds `review_large_diff_bytes`, the round-1 `doing-code-review` launch confirms the basis"); it does NOT restate the full magnitude recipe. This prevents a double-confirm (loop entry asks, then doing-code-review Step 1 asks again on the same base/head) and keeps one source of truth for the rule.
- **`review-loop` per-round re-resolve rule is untouched.** Step 0 gains a one-time entry check; the existing "re-resolve the file set every round" rule (`SKILL.md:41`) stays as the inter-round scope-drift guard. Do not collapse the two.
- **Threshold default 10240 even when the facts key is absent.** Both skills must function identically on repos without `review_large_diff_bytes` in `.ai-playbook/facts.md`.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: when the base is ambiguous, both skills instruct asking the user; when the diff exceeds the threshold, both instruct confirming the basis; when neither condition holds (small diff, obvious base), no new prompt is introduced.
- Consistency: the threshold key `review_large_diff_bytes` and the measure (`git diff <base>...<head> | wc -c`) are identical across both skills; default 10240 is stated in both.
- Minimal blast radius: no edits to `review-plan`, `review-confluence-doc`, `receiving-code-review`, `review-staging`, `review-agents`. The one validator change (Task 4) is a header-skip regex fix with a RED→GREEN self-test; no mechanical-gate or `source_digest` schema change.

**Release gates:**
- Public-hygiene scan (`bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`) exits 0; no personal paths / sensitive content introduced.
- Both edited skills read top-to-bottom with no broken markdown, no stale `<base>` placeholder left without a resolution path.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill Markdown):**
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

**Validator (code):**
- `scripts/validate_review_staging.py` *(existing file; Task 4 fixes the discarded-findings header skip pattern)*

**Tests:**
- *(none; these are doc/skill edits; validation is grep + hygiene scan, not a test suite)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-plan/SKILL.md`; reviews a document as-is, no diff/basis concept.
- `agents/skills/review-confluence-doc/SKILL.md`; reviews fetched page content, no before/after diff.
- `agents/skills/receiving-code-review/SKILL.md`; addresses existing PR threads, no diff base.
- `agents/skills/review-staging/SKILL.md`; spec skill (declares `source_kind`/`source_digest` schema), not a reviewer.
- `agents/skills/review-agents/SKILL.md` and `review-panel-selection.md`; shared catalog, inherits each orchestrator's framing.

**Review-fold note (from the r1 review):** the r1 sub-agent reported two validator drift items. One was **wrong**: `--source-plan` **is** implemented (lines 2524, 2557-2603) with a full self-test (`_selftest_source_plan_cli`, lines 2398-2464); no fix needed. The other was **confirmed** and is folded in as Task 4: the discarded-findings header skip pattern (line 380) matches only `| Agent |` while the authoritative templates mandate `| Worker |`.

## Validation Commands

```bash
# Both skills carry the explicit-basis rule (ask when base not obvious)
grep -n "ask the user" agents/skills/doing-code-review/SKILL.md agents/skills/review-loop/SKILL.md

# Both skills carry the magnitude rule + the shared threshold key
grep -n "review_large_diff_bytes" agents/skills/doing-code-review/SKILL.md agents/skills/review-loop/SKILL.md

# The shared default is stated in both skills
grep -n "10240" agents/skills/doing-code-review/SKILL.md agents/skills/review-loop/SKILL.md

# No stray edits leaked into the out-of-scope skills
! grep -rn "review_large_diff_bytes" agents/skills/review-plan agents/skills/review-confluence-doc agents/skills/receiving-code-review agents/skills/review-staging agents/skills/review-agents

# Public-hygiene gate (exit 0 required before commit)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

# Task 4: registers the new discarded-header case in the existing --selftest table
python3 scripts/validate_review_staging.py --selftest
```

## Tasks

### Task 1: Add explicit-basis + large-diff rules to `doing-code-review`

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [x] Insert a **"Resolve the comparison basis"** subsection at the top of `## Step 1: Gather Context` (before the existing "For a GitHub PR URL…" paragraph at line 50). State:
  - PR URL → base/head resolve unambiguously via `github-pr-workflow`; this is the "obvious" case, no prompt.
  - Branch review, base not obvious → **do not leave `<base>` as a placeholder**. If the base cannot be resolved with confidence (no `against X` arg, no single open PR, ambiguous integration branch), resolve it via the tier fallback (repo default integration branch per `AGENTS.md`). Then:
    - **Interactive top-level session:** ask the user explicitly, "What branch/commit should I diff against?" (or confirm the resolved default) before any `git diff` or sub-agent launch.
    - **Non-interactive / sub-agent context (risk-F1):** when invoked as a sub-agent of `execute-plan` Phase 3 or `review-loop`, or in a session with no user at the console (CI/scheduled), do NOT prompt. Accepting the resolved default is required to honour `execute-plan`'s "no asking between steps" contract (`execute-plan/SKILL.md:27`). **Record the resolution + reason in the staging-doc Metadata** (e.g. `Base resolved non-interactively: main (repo default; no PR/arg, autonomous sub-agent)`) so it is auditable rather than silent. The prompt fires only in an interactive top-level session.
  - Magnitude check (all modes): after resolving the base, run `git diff <base>...<head> | wc -c`. If the byte count exceeds `review_large_diff_bytes` (default `10240`), the change is unexpectedly large. In an interactive top-level session, **confirm the basis with the user before launching sub-agents** (state the size and proposed base, proceed only once the user confirms). **Decline path:** if the user does not confirm (declines, names a different base, or aborts), re-resolve to the corrected base and re-run the magnitude check, or stop; do not launch against an unconfirmed base. **Non-interactive context:** skip the confirmation prompt (the orchestrator's autonomy contract takes precedence) but still record the diff size and the resolved base in staging Metadata.
  - **Reading the threshold (correctness-F2):** this skill has two facts-reading sites, the line-9 `**Documentation paths:**` preamble (reads `{reviews_dir}`/`{tmp_dir}`) and the later `### Resolve paths from facts` subsection (~line 85). Because the magnitude check runs in Step 1 (~line 50), **before** the `### Resolve paths from facts` subsection, pin the threshold read to Step 1 itself: read `review_large_diff_bytes` from the opening TOML block in `.ai-playbook/facts.md` (same source as the line-9 preamble) inline in the magnitude-check bullet; absent key ⇒ default `10240`. Do not defer the read to the later subsection.
- [x] Keep the existing "Pull latest commits" / `git diff --name-only` / `--stat` block (lines 54-64); it now runs *after* the basis is resolved/confirmed. No change to those commands.
- [x] Add one bullet to `### Anti-patterns` (after line 45): "Silently inferring the diff base for a branch review, or proceeding when the basis is ambiguous: ask the user for the comparison base instead. Leaving `<base>` as a literal placeholder in a branch review is this anti-pattern."
- [x] Run → expect: `grep -n "review_large_diff_bytes" agents/skills/doing-code-review/SKILL.md` returns hits in Step 1 (magnitude rule) **and** `grep -n "confirm the basis with the user" agents/skills/doing-code-review/SKILL.md` returns a Step 1 hit. (The Anti-patterns bullet alone must not satisfy this gate, so do not OR in `"ask the user"`.)
- [x] Commit: `review: require explicit comparison basis and confirm large diffs in doing-code-review`

### Task 2: Add explicit-basis + large-diff rules to `review-loop` (Step 0, once at entry)

Files:
- `agents/skills/review-loop/SKILL.md`

- [x] Rewrite the **"Base branch"** resolution block (lines 33-37) so tier 3 is no longer a silent default:
  - Tier 1 (user named it via `against X` / PR base URL), unchanged, unambiguous.
  - Tier 2 (open PR for `HEAD_BRANCH`: base from `gh pr view` / `github-pr-workflow`), unchanged, unambiguous.
  - Tier 3 (neither applies), resolve to the repo default integration branch per `AGENTS.md`. Then, in an **interactive top-level session**, ask the user to confirm that base before round 1; in a **non-interactive / sub-agent context (risk-F1)**, accept the resolved default without prompting. Either way, **record the resolved base + reason in the staging-doc Metadata** so the resolution is auditable rather than silent.
- [x] **Magnitude guard: delegate, do not duplicate (design-simplicity-F1).** `review-loop` Step 1 *is* a `doing-code-review` launch (`SKILL.md:49,164-165`), and Task 1 arms `doing-code-review` Step 1 with the magnitude-confirmation rule. So Step 0 must NOT restate the full magnitude recipe (that would double-confirm on round 1 and create two copies that can drift). Instead add **one sentence** after base resolution, before the existing **"Diff scope"** paragraph (line 39): "If `git diff ${BASE_BRANCH}...HEAD | wc -c` exceeds `review_large_diff_bytes` (default 10240), the round-1 `doing-code-review` launch confirms the basis with the user (interactive) or records it in Metadata (non-interactive)." That is the entire loop-side magnitude handling.
- [x] **Read `review_large_diff_bytes` from the opening TOML block in `.ai-playbook/facts.md`** (same source as `{reviews_dir}`/`{tmp_dir}`); absent key ⇒ default `10240`.
- [x] **Facts-reading ordering / orphan-duplicate hazard (F4 + correctness-F3):** Step 0 currently reads `{reviews_dir}`/`{tmp_dir}` from facts at **line 43**, *after* where the magnitude-guard sentence lands (~line 39) and *after* the protected "Re-resolve the file set every round" rule at **line 41**. Move the facts-reading sentence to **before** the magnitude-guard sentence so the threshold is resolvable; **delete the original line-43 sentence** (do not leave an orphan duplicate); keep the line-41 "Re-resolve the file set every round" block **verbatim** during the relocation.
- [x] Update the **Quick prompt** (lines 158-160): clarify `<base>` is requested if not named and the diff is confirmed if large (e.g. append a sentence: "If no base is named or the diff is large (>10 kB), the loop asks you to confirm the comparison base before round 1 (skipped silently in non-interactive sub-agent runs, with the resolution recorded).").
- [x] Do **not** touch the per-round "Re-resolve the file set every round" rule (line 41) or the staging-doc schema.
- [x] Run → expect: `grep -n "review_large_diff_bytes" agents/skills/review-loop/SKILL.md` returns a Step 0 hit (the delegating guard) **and** `grep -n "round-1 .doing-code-review. launch confirms" agents/skills/review-loop/SKILL.md` returns a hit. The full magnitude recipe (`wc -c` + confirm + decline-path) must appear ONLY in `doing-code-review`, not restated here.
- [x] Commit: `review: require explicit comparison basis and confirm large diffs in review-loop`

### Task 3: Verify scope, consistency, and hygiene

- [x] Run → expect empty (no leaked edits): `grep -rn "review_large_diff_bytes" agents/skills/review-plan agents/skills/review-confluence-doc agents/skills/receiving-code-review agents/skills/review-staging agents/skills/review-agents`
- [x] Run → expect both skills state the default: `grep -n "10240" agents/skills/doing-code-review/SKILL.md agents/skills/review-loop/SKILL.md`
- [x] Run → expect exit 0: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- [x] Read both edited sections in full to confirm no broken markdown and no stale `<base>` placeholder left without a resolution path.

### Task 4: Fix discarded-findings header skip pattern in the validator

Files:
- `scripts/validate_review_staging.py`

**Defect:** `validate_discarded_findings` (line 380) skips a table header only when it matches `^\|\s*Agent\s*\|`. The authoritative templates mandate `| Worker | Worker severity | Pattern | Theme | Reason | Notes |` (`review-staging/SKILL.md:156`, `review-plan/SKILL.md:152`). Result: a correctly-formatted `| Worker |` header row is parsed as a data row, its `reason` cell (`Worker severity`'s neighbour) is read as the discard reason, and the validator emits a spurious `unknown discard reason code:` WARN. This surfaced during this plan's own r1 review (the artifact used the correct `| Worker |` header and was WARN'd). The canonical fixture `_current_clear_markdown` uses `None.` for the Discarded section, so the header-skip path is never exercised today, which is why the bug survived.

- [x] **RED**. Add a self-test `_selftest_discarded_header_skip(root, check)` alongside `_selftest_source_plan_cli` (line 2398) and register it in the `run_selftest` table (~line 2485, after `source_plan_cli`). Build the fixture by reusing `_current_clear_markdown`/`_current_clear_payload` (as `_selftest_source_plan_cli` does at lines 2419-2425) and **injecting** a populated Discarded section in place of its `None.`; the fixture MUST be a full current-format staging doc, NOT a stub (a stub fails `validate_staging_file` for unrelated structural reasons: missing `## Metadata`/`## Review Statistics`/`### Panel`). The injected Discarded section contains: a `| Worker | Worker severity | Pattern | Theme | Reason | Notes |` header row, the `|---|` separator, **two** data rows, one valid (`duplicate`) and one with a BAD reason (e.g. `not-a-real-reason`). Assert via `validate_staging_file(...)` that `result.warnings` is **non-empty** and contains `unknown discard reason code:` (testing-F2: assert on `result.warnings`, NOT `result.ok`; `add_warning` does not flip `ok` at lines 148-149, so an `result.ok` assertion would false-pass). Pre-fix this FAILS in the discriminating way: the `| Worker |` header is read as a data row → `reason="Reason"` → spurious warning. Run → expect RED: `python3 scripts/validate_review_staging.py --selftest` exits non-zero on the new case.
- [x] **GREEN**. Fix line 380 to skip the header when its first cell is `Agent` **or** `Worker`: replace `re.match(r"^\|\s*Agent\s*\|", line)` with `re.match(r"^\|\s*(?:Agent|Worker)\s*\|", line)`. This relies on the existing separator-row skip at **line 382** (`^\|[-:| ]+\|$`) to skip the `|---|` divider between header and data; do not remove line 382 (contract-docs-F2). Post-fix, re-run the self-test and assert: the spurious header warning is GONE **and** the BAD-reason data row STILL produces `unknown discard reason code:` (testing-F1: the negative-twin row proves the fix did not over-skip genuine data rows). Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` exits 0 with the new case passing both assertions.
- [x] Confirm the existing `_current_clear_markdown` fixture is unchanged (its `None.` Discarded section still returns early at line 375-376) and no other self-test regresses.
- [x] Commit: `validate: skip Worker-headed discarded-findings rows (not just Agent)`
