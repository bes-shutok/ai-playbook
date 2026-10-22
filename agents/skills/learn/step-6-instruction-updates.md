## Step 6: Instruction File Updates

Update instruction rules only in the repo’s existing instruction sections (typical names: reusable engineering rules, repository style and conventions, repository constraints; exact headings vary by repo).

### Instruction placement ladder (required before any edit)

Resolve canonical homes from `user_facts_path` keys; never hardcode language, stack, or tool names in this ladder.

| Scope | Canonical home (facts key or path) | Always-loaded instruction file |
|-------|-----------------------------------|--------------------------------|
| Cross-project universal | file under `shared_docs_dir` (for example `coding_guidelines.md`) | one-line cross-reference only |
| Stack or language ecosystem | appropriate file under `shared_docs_dir` | one-line cross-reference only |
| Company-wide | `company_guidelines_master` | one-line cross-reference only |
| Project / repo | `project_guidelines_rel` | one-line cross-reference only |
| Infrequent workflow | dedicated skill (`SKILL.md`) | remove from always-loaded instructions |
| Repo delta with no canonical home | (none) | full text allowed (keep concise) |

**Hybrid rule (mandatory):** When full rule text lives in a canonical tier, the instruction file gets **at most one line** (`see … #N` or equivalent pointer). Do **not** restate the same rule inline in the same bullet.

Placement test:
- reusable anywhere -> section 1
- repo consistency/look-alike -> section 2
- hard limit/prohibition -> section 3
- when unsure -> section 1

Instruction consolidation pass (required):
- Scan updated instruction files for overlapping bullets that prescribe the same behavior.
- Group overlaps into one canonical rule per intent; keep wording explicit and enforceable.
- Remove weaker/ambiguous duplicates instead of keeping multiple variants.
- If two rules are both needed, make scopes non-overlapping and clearly distinguish baseline rule vs exception rule.

Compaction pass (required):
- When an instruction rule restates or elaborates a convention already fully documented in company or project guidelines, replace the rule body with a compact reference (for example `see company-guidelines.md #N` or `see project-guidelines.md #N`) and keep only the incremental constraint or local exception in the instruction file. Edit the **canonical** file for the tier (`company_guidelines_master` or `project_guidelines_rel` per facts keys), not a repo company mirror alone.
- When a rule in a project-level instruction file (`repo AGENTS.md`) duplicates content already present in user-level instructions (`~/.codex/AGENTS.md`), remove the project-level duplicate or reduce it to a one-line cross-reference. User-level rules are always loaded; restating them per-project adds no enforcement value and creates drift risk.
- When adding a NEW project-specific technical or architectural convention (for example persistence configuration, test infrastructure pattern, schema layout, tool-specific settings), place the detailed content as a numbered rule in the current repo's project guidelines (`project_guidelines_rel` facts key) first; add only a one-line `see project-guidelines.md #N` reference in instruction files. Full-text rules in instruction files are reserved for cross-cutting reasoning guards that have no suitable canonical doc home.
- When adding a NEW cross-repository convention or baseline standard, choose the canonical home by scope. Read `user_facts_path` and resolve:
  - **Universal coding principle** (applies in any language, any company): `<shared_docs_dir>/coding_guidelines.md`
  - **Ecosystem-specific** (shared across JVM languages, Spring Boot patterns, Reactor/Mono): `<shared_docs_dir>/jvm_guidelines.md`, not in `coding_guidelines.md` because ecosystem rules are irrelevant to Python/Go/Rust projects.
  - **Language/framework-specific** (Kotlin stdlib idiom, MockK, Java Optional): `<shared_docs_dir>/kotlin_guidelines.md` / `java_guidelines.md` etc.
  - **Company-specific convention** (naming, error code format, logging policy shared across company repos but not universal): **`company_guidelines_master`** (facts key), not `company_guidelines_repo_mirror_rel`; sync repo mirrors after editing the master.
  - Do NOT default to company guidelines for general programming principles; that file is for company-specific conventions only.
  - Add only a one-line `see company-guidelines.md #N` reference in instruction files (repo-relative label for humans; canonical edit target remains the facts key).
- When multiple instruction bullets share the same governing principle, merge into one generalized rule with examples rather than keeping N specific variants.
- When a rule can be stated more concisely without losing its enforceable meaning, shorten it; prefer one-sentence rules over multi-sentence explanations.
- Byte-budget compaction fidelity audit: when rewriting or condensing an instruction bullet to fit the size budget, diff-audit the rewrite against its canonical source so every enumerated option, example, and qualifier survives (e.g. a three-option rule must not surface as two options; named fixture examples must not be dropped). Saving bytes never authorizes silently removing a rule element; if the element does not fit, move it to the canonical doc and leave a pointer.
- When an instruction rule is only needed for specific infrequent task types (for example Jira story creation, PR description writing, PR chunk splitting), move it to a dedicated skill such as `jira-pr-workflow` rather than keeping it in the always-loaded instruction files; add or update the trigger description in the skill's front matter.
- Do not remove a rule solely to save space; only when the canonical doc or a more general rule already covers it.

## Step 6.5: Instruction size gate (required before finishing learn)

Always-loaded instruction entrypoints (`AGENTS.md`, `CLAUDE.md`, and repo-root copies when present) are a fixed context budget, not a second canonical doc tier. Canonical guideline files (`project_guidelines_rel`, company master, `shared_docs_dir`) stay **on demand** (open only the sections or `#N` rules the task needs); compaction moves full rule text there and leaves pointers in entrypoints.

**Budget:** **30,720 bytes** per instruction entrypoint.

1. From the repo root, run:
   ```bash
   "${HOME}/.ai-playbook/scripts/check-instruction-size.sh" check
   ```
   (Override script path only for local testing via `INSTRUCTION_SIZE_CHECK_SCRIPT`.)
2. When **check** fails (any listed file exceeds the budget), run the compaction pass in Step 6 **in this learn run** until **check** passes: replace hybrid bullets with cross-references, move infrequent workflow rules to skills, and keep only repo deltas without a canonical home.
3. Do not finish learn while instruction files remain over budget after placement.

**Net-growth rule:** When adding a cross-reference to an instruction file, do not increase file size unless an equal or larger amount of redundant inline text was removed in the same learn run.

## Step 6.6: Corpus gates (required before finishing learn)

Two corpora, two gates:

| Corpus | Path | Gate |
|--------|------|------|
| **User-level** (cross-project, strict `UL#N`) | resolved from `shared_docs_dir` / runtime symlink | **Step 6.6 script** below (the lessons hub: `lessons.py index`) |
| **Project-level** (convention `#N`) | `docs/maintenance/development_lessons.md` | **Skill-gate learn class** (PreToolUse hook; refresh `learn.*.marker` before every Write/Edit per the skill-gate README) |

The project corpus IS skill-gate gated: absent or stale `learn.<project>.<session>.marker` blocks Write/Edit to `development_lessons.md` with `Invoke the learn skill before editing the project lessons corpus.` The user-level corpus is NOT skill-gate gated; it remains opt-in strict via the script gate in this step only.

**Commit ownership:** `learn` writes the corpora and commits only its own learn-authored skills-repo artifacts (Step 1.8; the skill-placement commit workflow); the project lessons corpus itself is committed by `done` Step 3 when it is not gitignored; that commit must stage the corpus by own-edit hunk after the Step 1.8 word-diff own-edit check, never whole-file, so a peer's uncommitted lesson is skipped and reported rather than swept into the committer's commit (lesson 134 is the class); do not treat orphan `docs` sync as a substitute for that commit.

### User-level lessons-corpus gate (script)

The user-level corpus is opt-in strict: lessons captured as cross-project (`UL#N`) must carry a `**Principle:** Family X` (or `Family excluded (<kind>)`) tag so the corpus stays grep-indexable and the `generalize` audit does not lose them. This subsection enforces that invariant on the **user corpus only** before learn finishes.

Resolve (do NOT reference the upper-case shared-docs-dir env var - it is not exported; the facts key is lowercase `shared_docs_dir`, and the upper-case form expands to empty, collapsing the path and silently tripping the missing-corpus cold-start guard):
- script: `script="${LESSONS_INDEX_SCRIPT:-${HOME}/.ai-playbook/scripts/lessons.py}"` plus subcommand `index` (`LESSONS_INDEX_SCRIPT` override is local-testing only; the hub owns ALL lessons CLI dispatch, so the gate runs `"$script" index "$user_corpus"`, never a direct module invocation whose standalone dispatch moved into the hub)
- user corpus: `user_corpus="${HOME}/Projects/.ai-playbook/development_lessons.md"` (runtime symlink, canonical-equivalent to the `shared_docs_dir` master)

Guards, in order:

1. **Drift precheck (warn-only):** if the repo source AND runtime copies exist AND `diff -q` differs for `lessons_corpus.py` OR `lessons_index.py` OR `lessons_adopt.py` OR `lessons_migrate.py` OR `lessons.py`, warn naming the drifted script(s) and give the `cp` repo->runtime recipe; continue. If the repo source is absent (runtime-only deployment), emit a WARNING (not a silent note) that the gate's own integrity is unverified and continue. Warn-only because blocking would deadlock the very `learn` that could fix the drift.
2. **Missing-script cold-start:** `[[ -f "$script" ]]` or warn "gate script absent; install via the playbook repo" and exit 0.
3. **Missing-corpus cold-start:** if the user corpus file does not exist (playbook not cloned / convention not adopted at user level yet), warn "user-level corpus absent; see `coding_guidelines.md` #17; run `lessons-migrate` to seed it" and exit 0.
4. **Zero-tag cold-start:** if the user corpus has zero family tags, warn "convention not adopted in user corpus" and exit 0.
5. **Adopted (blocking):** run `"$script" index "$user_corpus"`. On non-zero exit, print the recovery recipe for the reported validator category and **block** (exit 1). Each listed `UL#N` carries exactly one category (`duplicate` | `untagged` | `multiple-tags` | `invalid-family`, classified in that precedence order by `lessons_index.py`), and the recipe branches on it; the recovery is operator-driven - it never renumbers lessons or rewrites cross-references itself, and every listed edit is a deliberate operator change. `lessons.py adopt` (the `lessons_adopt` library's manual tool) is NEVER invoked automatically - do NOT route it through `done`:
   - `duplicate`: two headings claim one `UL#N` (the silent-overwrite hazard). Inspect the colliding headings, choose a unique identifier for the colliding lesson, update the same-corpus references to the renumbered id by hand, then re-run the validator. A duplicate is a heading collision, not a tagging case: no tag backfill rewrites anything here.
   - `untagged` / `invalid-family`: the tagging/adoption workflow applies - classify the listed `UL#N` via learn/generalize, OR run `lessons.py adopt --tag-unclassified <user_corpus>` manually, then re-run `learn`.
   - `multiple-tags`: classify the lesson first, then remove the competing family tags so exactly one `**Principle:** Family X` line remains outside fenced blocks, then re-run the validator.

**Block propagation (r4 Medium 4):** `learn` is invoked by `done` Step 1 as a SKILL (a sub-procedure, not a subprocess whose exit code `done` checks). "Step 6.6 blocks (exit 1)" therefore means the `learn` skill returns `blocked` to its caller; `done` Step 1 treats a blocked `learn` as a Step-1 failure (does NOT proceed to Step 2 commit) and falls through to `done`'s Step 6 lock-release. The operator fixes the user corpus out-of-band before the next `done`. A standalone `learn` (not under `done`) must NOT trigger `lessons.py adopt`.

**Strictness trade:** a `learn` in any project blocks on a user-corpus violation because the user chose strict user-level. The corpus is single-user-local, so a block means "fix the user corpus", not "fix this repo". This is intentional: one strict corpus enforces the tag invariant across every project's `learn` run.

**Project-tier dup check (warn-only):** project `development_lessons.md`: optional `grep -oE '^## [0-9]+' <project_corpus> | sort | uniq -d` (warn-only; the user-corpus validator's `duplicate` category via `lessons.py index` is the blocking shape a later project-tier promotion would reuse). Project corpus writes are enforced by the skill-gate learn class at edit time, not by this script step.

### Lesson concision gate (required before finishing learn)

Lessons are reference material read mid-task, not prose to admire. A lesson that rambles gets skimmed and the rule is lost  -  the failure mode the `i-have-adhd` skill exists to prevent. Before finishing, apply this gate to every new or substantially edited lesson (user-level `UL#N` and project `#N`):

1. **Word budget:** a single lesson block should sit near the corpus median, not multiples of it. After drafting, `wc -w` the block (from its `## N.` header to the next `## ` header). If it is more than ~1.5× the median of the last 10 same-corpus lessons, tighten it. The Principle/Trigger/Rule/Why/Shape/Example/See-also skeleton stays; the *words inside each* get cut.
2. **One discriminator, not three.** A lesson may need one "Distinguishing from #X" subsection when a sibling lesson is a near-miss. Two or more discriminator subsections is a sign the lesson is bundling multiple principles  -  split it, or fold the distinctions into the General form line.
3. **No restating the rule in the example.** The Example section shows the incident; it must not re-derive the rule. If the Example paragraph restates Rule steps, cut the restatement.
4. **Sentences under control.** No sentence should run past ~40 words. Long compound sentences with multiple em-dash/parenthetical asides are a red flag  -  split them. (Apply the `i-have-adhd` shaping rules: lead with the next action, number multi-step rules, cut tangents.)
5. **Title under control.** The `## N.` title is a scannable label, not an abstract. If it exceeds ~12 words or contains a semicolon, shorten it (the detail belongs in Principle/Rule, not the header).

This gate is blocking: if a lesson is over budget after one tightening pass, either cut more or split the lesson. Do not finish learn with an over-long lesson in the corpus.

## Step 7: API Contract Naming Hygiene
When lessons involve external API naming or endpoint shape:
- Prefer resource-oriented OpenAPI paths and avoid RPC verb segments (`/set`, `/check`, `/resolve`, `/merge`, `/unsuppress`).
- Use kebab-case for multi-word path segments and consistent module-aligned roots.
- Record old-to-new endpoint mapping and rationale in canonical docs (`docs/project-decisions.md`) as documentation-only deprecation context.
- If API path or `operationId` renames were already made in the implementation workflow, verify docs remain synchronized with those changes; do not perform implementation refactors as part of this learn workflow.
