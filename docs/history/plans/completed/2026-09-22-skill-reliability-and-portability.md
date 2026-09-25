# Plan: skill reliability and portability

Backlog origins: `docs/history/backlog/2026-09-19-plan-authoring-skill-invocation-pin.md`, `docs/history/backlog/2026-09-21-audit-review-agents-for-portability.md`, `docs/history/backlog/2026-09-21-automate-skill-version-drift-repair.md`

## Terms

- **Shared catalog**: a file under `agents/skills/review-agents/` consumed by multiple orchestrating skills. Must stay language-agnostic and project-agnostic: abstract failure shapes, detection patterns, and evidence requirements only.
- **Language overlay**: stack-specific guidance files resolved from `shared_docs_dir` in the user facts document (for example JVM, Kotlin, or Python guideline files). The home for language-specific behavior.
- **Guideline Pack**: project-specific conventions resolved from facts and sibling-repository evidence. The home for runner names, harnesses, paths, and commands.
- **Placement marker**: the literal HTML comment `<!-- portability: abstract -->` appearing in a catalog line. Recognized position-independently (the exact token anywhere in the line); in a GFM table row it rides in the final cell after the cell text, never as a new pipe column. Declares that the line's language, framework, or product tokens are an explicitly abstract illustration; excuses that line from the portability checker.
- **Version stamp**: an optional version field in a skill's `SKILL.md` frontmatter, read from the nested `metadata.version` form (the existing repository convention; `agents-best-practices` is the sole precedent) or a top-level `version:`. Stamps compare with numeric-aware dot-segment ordering (each dot-separated segment compares as an integer; never lexical, so 10 compares above 9). Orderable when present on both sides; enables older/newer classification.
- **Platform destination**: a root directory holding an installed copy of a skill (for example `~/.agents/skills`, `~/.claude/skills`, `~/.cursor/skills`, `~/.codex/skills`). Destinations are resolved through symlinks to physical paths before comparison; agent-managed autonomous stores are excluded from defaults per the repository vendoring rules.
- **Classification vocabulary** (distribution check): `MISSING` (no copy at the destination), `CURRENT` (content digest equals the source), `STALE` (digest differs and the stamp pair is absent, unordered, or equal; drift direction unknown, overwrite requires the downgrade consent flag), `OLDER` (destination stamp orders below source), `NEWER` (destination stamp orders above source), `SKIP` (destination resolves to the source tree itself; reported, never written). Symlink-aliased destinations are deduplicated to physical paths BEFORE classification: one physical copy reports once with its alias paths named, and that row carries the physical copy's own classification (an aliased drifted registry is STALE and exits 1, never masked as SKIP).
- **Skill-gate marker**: the consent marker the plans skill refreshes before every plan-file write, at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`. `project` derives via `facts_paths.resolve_project_key` from the repository anchor; `session` derives from the output of `python3 ~/.ai-playbook/scripts/session_channel.py`: empty after stripping means the literal `no-session`, otherwise `sha1(value)` truncated to 16 hex characters. Recorded here as this plan's own authoring-session gate contract per the skill-gate README single-source rule; no plan task writes gated files at execution time.
- **Execution contract**: the section of this plan binding any execution session to the claim-file, stand-down, and no-push rules.

## Execution Contract

- **Claim file**: before the first task, an execution session writes `docs/tmp/claims/2026-09-22-skill-reliability-and-portability.claim.md` recording the session identity, the plan path, and the plan byte digest. A session finding an existing live claim by another session stands down instead of duplicating.
- **Stand-down guard**: before each task, re-check the claim file and `git status --porcelain`. Stand down when another session has committed plan-owned paths, when the plan file is archived, or when the claim file shows a newer live owner.
- **No push**: all work stays local. No branch is pushed at any point.

## Assumptions

- assume one plan covers all three origins; basis: the dispatching request names a single titled plan and the origins share the skill-layer reliability root.
- assume the authoring pin appends a new numbered principle instead of renumbering the existing list; basis: cross-skill references cite existing principle numbers, and appending keeps them stable.
- assume the deliverable for origin 1 is the repository-canonical `agents/skills/using-skills/SKILL.md`; the documented `~/.agents/hooks/session-start.sh` does not exist on the authoring host, and the deployed-copy update follows the existing vendoring flow; basis: on-disk verification 2026-09-22.
- assume `agents/skills/graphify/` stays unedited (vendored upstream copy); wiring the distribution check into its preflight is an upstream concern; basis: vendored-asset sync rules in the repository guidelines.
- assume the portability checker uses deny patterns plus a placement-marker allowlist; basis: the origin acceptance requires exceptions documented by placement.
- assume version stamps are optional frontmatter fields read from the nested `metadata.version` form (the existing convention, sole precedent `agents-best-practices`) or a top-level `version:`; the corpus carries almost no stamps, so stampless drift is the common case and the consent guard, not the version path, is the main protection; basis: on-disk frontmatter verification 2026-09-22.
- assume default destinations enumerate the standard home agent skill roots resolved through symlinks and deduplicated to physical copies, excluding agent-managed autonomous stores; on the verified authoring host the managed roots alias one physical registry, so defaults collapse to that single physical copy; basis: `projects/.ai-playbook/agent-runtime-layout.md` and host verification 2026-09-22.

Decision points requiring a grill: none remain.

## Gist & Examples

Three witnessed failure families share one root: the skill layer is consumed across runtimes and platforms but was authored from one.

**Family A, invocation pin.** Roughly 24 user corrections of the form "did you even use the plans skill" share a shape: an authoring-shaped ask without the literal word "plan" ("turn this backlog item into a plan" phrased as "how should we do X") did not bind to the `plans` skill, and environment-specific answers skipped the facts lookup. The SessionStart principles pin execute-plan invocation detection (principle 6) but have no authoring twin. The fix adds one principle: any plan-shaped deliverable invokes the `plans` skill regardless of phrasing, and environment-specific answers resolve from the facts file before memory.

**Family B, catalog portability.** The review-agent catalogs are shared guidance consumed by many orchestrators, but recent additions encode one stack: `review-panel-selection.md` names "Java/Spring, Kotlin/Spring, or Python" overlays and a "Kafka/RocketMQ consumers" risk row; `testing.md` names Java/Kotlin/C#, Python, Ruby, `UnsupportedOperationException`, `NotImplementedError`, Mockito, and `ArgumentCaptor`; `documentation.md` names Maven, Modulith, and `ModuleBoundariesTest`. The fix abstracts the witnessed violations, audits every catalog file, states the four-layer boundary (shared catalog, language overlay, Guideline Pack, orchestrator) in one place, and adds a regression checker so a new hardcoded assumption fails loudly with file and line.

**Family C, distribution integrity.** A stale installed skill was detected but the warning could not name which platform held the stale copy, so every platform needed manual inspection. The fix is a reusable check: enumerate configured platform destinations for a skill, resolve symlinks and deduplicate to physical copies, compare each copy against the source, report the exact stale platform paths with classification (missing, stale, older, newer, current, skip), offer an idempotent refresh, and exit nonzero when any destination remains non-current. The refresh never overwrites a destination whose drift it cannot prove older: only missing and provably older copies refresh by default; a stampless drifted copy or a version-newer copy needs the explicit downgrade consent flag, and a destination resolving to the source itself is never written.

Non-goals: no workflow-instruction duplication in the distribution checker; no network access; no edit to the vendored `agents/skills/graphify/` copy.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both new test suites pass under pytest; the checker's polarity is proven (exit 1 with file and line evidence on the unfixed tree, exit 0 after the catalog fixes).
- portability: the checker exits 0 over the whole `agents/skills/review-agents/` tree; every remaining language, framework, or product token sits on a line carrying a placement marker.
- reliability: the distribution check distinguishes MISSING, STALE, OLDER, NEWER, CURRENT, and SKIP; refresh is idempotent including the extraneous-file drift shape; a stampless drifted destination or a version-newer destination is preserved unless the explicit downgrade flag is passed; alias destinations report once; exit is nonzero while any destination remains non-current.
- maintainability: both scripts are stdlib-only, standalone, and runnable before and after deployment via the existing runtime-script deployment conventions.

**Done when:**
- `python3 -m pytest scripts/test_check_review_agent_portability.py scripts/test_skill_distribution_check.py -q` passes.
- `python3 scripts/check_review_agent_portability.py` exits 0 over the repository catalog tree.
- The authoring pin greps in the Validation Commands block all pass.
- The consumer boundary contract exists in `agents/skills/review-agents/SKILL.md` and consumer citations name the boundary instead of stack specifics.
- The repository guidelines mandate the checker for changes touching `agents/skills/review-agents/`.

**Ship when:**
- The next user-corrections mining pass records no new "you should have used plans skill" corrections; human-owned observation window, `operational follow-up`, evidence owner: the corrections-mining pass, closure: one clean mining cycle.
- The upstream graphify project wires a skill-distribution preflight call; external prerequisite owned by the upstream project; this repository's check is callable and documented for that wiring.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_review_agent_portability.py` *(new)*
- `scripts/skill_distribution_check.py` *(new)*
- `AGENTS.md` (one wiring sentence in the testing-guidance section; the rest of the file is frozen)
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/SKILL.md`

**Tests:**
- `scripts/test_check_review_agent_portability.py` *(new)*
- `scripts/test_skill_distribution_check.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. Concretely: additional files under `agents/skills/review-agents/` that the Task 3 audit finds violating; `agents/skills/review-agents/architecture.md` if the boundary statement lands there; consumer `SKILL.md` files whose `review-agents` citations are corrected under Task 3.

**Out of scope; reject unless plan-related:**
- `agents/skills/graphify/**`; vendored upstream copy, local edits create sync drift.
- `docs/history/backlog/**`; origin items move via the completion flow, not this plan.
- Host-level runtime directories (`~/.agents`, `~/.claude`, `~/.cursor`, `~/.codex`); outside the repository.

## Validation Commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Family B: portability checker green over the real catalog tree (rule 13: anchored to repo root)
python3 scripts/check_review_agent_portability.py || { echo 'FAIL: portability checker reported violations'; exit 1; }

# Both new test suites
python3 -m pytest scripts/test_check_review_agent_portability.py -q || { echo 'FAIL: portability checker tests'; exit 1; }
python3 -m pytest scripts/test_skill_distribution_check.py -q || { echo 'FAIL: distribution check tests'; exit 1; }

# Family A: authoring pin present, each distinctive span exactly once (rule 33: count gates, not presence)
test "$(grep -cF 'plan-shaped deliverable' agents/skills/using-skills/SKILL.md)" -eq 1 || { echo 'FAIL: authoring pin missing or duplicated'; exit 1; }
test "$(grep -cF 'regardless of phrasing' agents/skills/using-skills/SKILL.md)" -eq 1 || { echo 'FAIL: phrasing-independence pin missing or duplicated'; exit 1; }
test "$(grep -cF 'before answering from memory' agents/skills/using-skills/SKILL.md)" -eq 1 || { echo 'FAIL: facts-first reinforcement missing or duplicated'; exit 1; }

# Principle numbering stable: principles 6 and 10 keep their leading numbers after the append
grep -qE '^6\. ' agents/skills/using-skills/SKILL.md || { echo 'FAIL: principle 6 numbering regressed'; exit 1; }
grep -qE '^10\. ' agents/skills/using-skills/SKILL.md || { echo 'FAIL: principle 10 numbering regressed'; exit 1; }
test "$(grep -cE '^11\. ' agents/skills/using-skills/SKILL.md)" -eq 1 || { echo 'FAIL: principle 11 missing or duplicated'; exit 1; }

# Family B: consumer boundary contract present in the shared-catalog entry point
grep -qF 'Consumer contract' agents/skills/review-agents/SKILL.md || { echo 'FAIL: consumer contract section missing'; exit 1; }

# Family B: checker wired into the repository change discipline
grep -qF 'check_review_agent_portability.py' AGENTS.md || { echo 'FAIL: checker not wired into repository guidelines'; exit 1; }
```

### Task 1: Portability regression checker (RED first)

Files:
- `scripts/check_review_agent_portability.py` *(new)*
- `scripts/test_check_review_agent_portability.py` *(new)*

- [x] Write the test file first with the nine fixture tests below; run `python3 -m pytest scripts/test_check_review_agent_portability.py -q`, expect RED (module import error) [class: REPOSITORY_TEST]
- [x] Implement `check_review_agent_portability.py`: stdlib-only; scans `agents/skills/review-agents/*.md` (optional positional path arguments narrow the scan); deny-pattern categories are framework and product tokens, language-syntax tokens, build-tool invocations, test-suffix names, repository-absolute paths, and ticket-prefix shapes; each shipped pattern names its category and stays precise enough that ordinary stack-flavored detection vocabulary does not trip it; a line containing the placement marker `<!-- portability: abstract -->` is excused (position-independent recognition; in table rows the marker rides in the final cell); each violation prints `file:line: category: token`; exit 0 clean, exit 1 violations, exit 2 usage error [class: IMPLEMENTATION_REQUIRED]
- [x] `test_unmarked_framework_token_fails`; given a temp catalog line containing a Spring token without a placement marker, expects exit 1 and a report line naming the file, the line number, and the matched token [class: REPOSITORY_TEST]
- [x] `test_placement_marker_excuses_line`; given the same line carrying the placement marker, expects exit 0 [class: REPOSITORY_TEST]
- [x] `test_placement_marker_excuses_table_row`; given a GFM table row whose final cell carries the placement marker, expects exit 0 [class: REPOSITORY_TEST]
- [x] `test_repo_path_token_detected`; given a temp catalog line containing a home-anchored absolute path, expects exit 1 with the path category named [class: REPOSITORY_TEST]
- [x] `test_build_tool_token_detected`; given a temp catalog line containing a build-tool invocation token, expects exit 1 with the build-tool category named [class: REPOSITORY_TEST]
- [x] `test_test_suffix_token_detected`; given a temp catalog line containing a test-class suffix token, expects exit 1 with the test-suffix category named [class: REPOSITORY_TEST]
- [x] `test_ticket_prefix_detected`; given a temp catalog line containing a ticket-prefix shape, expects exit 1 with the ticket-prefix category named [class: REPOSITORY_TEST]
- [x] `test_language_syntax_token_detected`; given a temp catalog line containing a language-syntax identifier, expects exit 1 with the language-syntax category named [class: REPOSITORY_TEST]
- [x] `test_clean_catalog_passes`; given a temp catalog using only abstract wording, expects exit 0 [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 -m pytest scripts/test_check_review_agent_portability.py -q` [class: REPOSITORY_TEST]
- [x] Run the checker against the real tree → expect RED with the witnessed hits in `review-panel-selection.md`, `testing.md`, and `documentation.md` (this is the gate Task 2 flips) [class: REPOSITORY_TEST]
- [x] Commit: `skills: add review-agents portability regression checker` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Fix the witnessed catalog violations (checker GREEN on those files)

Files:
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/documentation.md`

- [x] `review-panel-selection.md` risk-signal paragraph: replace the parenthetical stack enumeration after "language overlay" with a pointer to the consuming orchestrator's mandatory-evidence rules; the stack enumeration belongs to the orchestrator layer, not the shared catalog [class: IMPLEMENTATION_REQUIRED]
- [x] `review-panel-selection.md` concurrency-scan table: abstract the stack tokens in ALL FOUR rows, not only messaging: Transactional scope becomes declarative transaction annotations, row-lock clauses, isolation-level configuration; Synchronization becomes language lock primitives, mutex types, virtual-thread pinning risks; Retry/backoff becomes retry-template abstractions, retryable-method annotations, rate-limit response mapping, circuit breakers; Messaging/async becomes message-broker consumers, outbox workers, async-method annotations, thread pools [class: IMPLEMENTATION_REQUIRED]
- [x] `testing.md` helper-matrix section: replace the mock-framework product name and its verification call name with "a mock-adapter never-invoked verification or the toolchain's equivalent" [class: IMPLEMENTATION_REQUIRED]
- [x] `testing.md` test-double and actionable-fix-snippet sections: rewrite the static-versus-dynamic sentences abstractly (statically-typed toolchains enforce at compile time; dynamically-typed toolchains need an explicit double-completeness assertion; unexercised methods raise the toolchain's canonical not-implemented error type), and in the actionable-fix-snippets passage replace the argument-captor class name with "the repository's argument-capture idiom" [class: IMPLEMENTATION_REQUIRED]
- [x] `documentation.md` module-README section: replace the build-tool, framework-module, and module-boundary-test product names with abstract shapes (dependency coordinates, module-boundary tests and API-surface annotations, which module imports which); in the adjacent Module high-level tasks section, replace the downstream contract abbreviation with "downstream API contracts" [class: IMPLEMENTATION_REQUIRED]
- [x] `documentation.md`: replace every API-documentation comment product name (the Javadoc and KDoc occurrences in the prose-clarity and keep-without-flagging passages) with "the toolchain's canonical API-documentation comment format" [class: IMPLEMENTATION_REQUIRED]
- [x] Checker-driven cleanup of the three witnessed files, applying THE disposition policy (this item is the policy's single home; Task 3 references it rather than restating it): run the checker scoped to the three edited files; for EVERY reported hit, abstract the wording, or keep the tokens under a placement marker with a one-line note naming the owning layer (language overlay, Guideline Pack, or orchestrator) when the token is a necessary abstract illustration or a facts-resolved overlay key; placement markers are for body lines only, so a heading or section-title hit is abstracted, or the section is relocated to its overlay home with a pointer; repeat until the scoped run exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the checker scoped to the three edited files exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `skills: abstract witnessed stack tokens in review-agent catalogs` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Complete-catalog audit and consumer boundary

Files:
- `agents/skills/review-agents/SKILL.md`
- `AGENTS.md` (change-discipline wiring sentence)
- consumer `SKILL.md` files named below

- [x] Run the checker over every file under `agents/skills/review-agents/`; for each remaining hit, apply the Task 2 disposition policy (its single home) [class: IMPLEMENTATION_REQUIRED]
- [x] Add or extend the boundary contract section (titled `Consumer contract`) in `agents/skills/review-agents/SKILL.md`, reconciling any existing boundary or layer table in that file into it rather than adding a parallel second contract; it states the four-layer boundary: shared catalogs carry abstract detection patterns and failure shapes; language overlays carry stack-specific behavior; the Guideline Pack carries project conventions, runners, paths, and commands; consuming orchestrators carry execution framing, tool choice, and output format [class: IMPLEMENTATION_REQUIRED]
- [x] Wire the checker into the repository's change discipline: add one sentence to the repository guidelines' testing-guidance section mandating `python3 scripts/check_review_agent_portability.py` (exit 0 required) whenever a change touches `agents/skills/review-agents/`, mirroring the existing hygiene-scan mandate [class: IMPLEMENTATION_REQUIRED]
- [x] Audit each consumer of the catalogs (`doing-code-review`, `review-plan`, `review-staging`, `review-reconciliation`, `receiving-review`, `generalize`, `how-to-write-skills`, `plans`, `rfc-design`, `review-confluence-doc`, `premortem`, `execute-plan/subagent-prompts.md`): where a consumer applies stack-specific guidance it must point at the facts-resolved overlay or Guideline Pack, not restate stack specifics inherited from a catalog example; fix over-claiming citations found [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/check_review_agent_portability.py` over the whole tree [class: REPOSITORY_TEST]
- [x] Commit: `skills: state review-agents portability boundary and complete catalog audit` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Authoring pin in the SessionStart principles

Files:
- `agents/skills/using-skills/SKILL.md`

- [x] Append principle 11 to the numbered Proactive Usage Principles: plan authoring binding. Any plan-shaped deliverable (author a plan for X, turn a backlog item into a plan, or a how-should-we-do-X question whose expected artifact is a plan) invokes the `plans` skill regardless of phrasing; the literal word "plan" is not required in the ask; environment-specific answers resolve from the repo facts file per Step 0 before answering from memory [class: IMPLEMENTATION_REQUIRED]
- [x] Do not renumber or reword principles 1 through 10; existing cross-skill references cite their numbers [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Family A grep gates from the Validation Commands block → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: pin plan-shaped asks to the plans skill in SessionStart principles` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Skill distribution integrity check

Files:
- `scripts/skill_distribution_check.py` *(new)*
- `scripts/test_skill_distribution_check.py` *(new)*

- [x] Write the test file first with the sixteen fixture tests below; run `python3 -m pytest scripts/test_skill_distribution_check.py -q`, expect RED (module import error) [class: REPOSITORY_TEST]
- [x] Implement `skill_distribution_check.py`: stdlib-only CLI `--skill NAME [--source DIR] [--dest ROOT]... [--refresh] [--downgrade] [--json]`; source defaults to the repository's `agents/skills/NAME` resolved from the repository root anchor (the git toplevel of the invocation cwd; never a cwd-relative concatenation); the default destination set is enumerated as the home-relative agent skill roots `~/.agents/skills`, `~/.claude/skills`, and `~/.cursor/skills` only, each resolved through symlinks to its physical path and deduplicated so one physical copy reports once with its alias paths named; agent-managed autonomous stores (for example `~/.codex/skills`, which the repository vendoring rules exclude) are never defaults and appear only via explicit `--dest`; a destination resolving to the source tree classifies SKIP and is never written; classification per the Terms vocabulary using a per-file digest set (sorted relative paths plus per-file content digests) plus optional frontmatter version stamps read from `metadata.version` or a top-level `version:`; one report line per distinct physical destination naming the platform root, the resolved path, alias paths, and the classification; `--refresh` copies only MISSING and OLDER destinations, requires `--downgrade` for STALE (unknown drift direction) and NEWER, replaces the destination directory with the source tree including removal of extraneous destination files, re-verifies after copying, and never touches the network; `--json` emits the same report machine-readably; every test fixture passes `--dest` explicitly, and every fixture except `test_default_source_resolves_from_repo_root` (which by design exercises the default) passes `--source` explicitly, so no test relies on default destinations and none traverses or writes the real home skill roots; exit 0 when all destinations are CURRENT or SKIP, exit 1 when any is not, exit 2 on usage error [class: IMPLEMENTATION_REQUIRED]
- [x] `test_default_source_resolves_from_repo_root`; given invocation from a subdirectory of a temp git repository holding the skill at `agents/skills/NAME` and no `--source`, expects the default source to resolve to the repo-root copy (no spurious MISSING); the temp repository lives in `mktemp -d` and the test tears it down [class: REPOSITORY_TEST]
- [x] `test_stale_sibling_detected`; given a destination holding a modified copy of a source skill, expects exit 1 and a report naming the destination path with classification STALE [class: REPOSITORY_TEST]
- [x] `test_missing_destination_reported`; given a destination root without the skill, expects a report line with classification MISSING and exit 1 [class: REPOSITORY_TEST]
- [x] `test_stampless_drift_requires_consent`; given a destination with no version stamps whose content differs from the source, expects plain `--refresh` to leave the destination unchanged with exit 1 and a report naming the consent requirement, and `--refresh --downgrade` to converge it [class: REPOSITORY_TEST]
- [x] `test_equal_stamp_differing_digest_requires_consent`; given a destination whose stamp equals the source stamp but whose content differs, expects classification STALE and destination bytes unchanged without `--downgrade` [class: REPOSITORY_TEST]
- [x] `test_version_ordering_numeric`; given a destination stamped 10.0.0 against a source stamped 9.0.0, expects classification NEWER (numeric segment order, not lexical) [class: REPOSITORY_TEST]
- [x] `test_older_destination_refreshes_by_default`; given a destination whose stamp orders below the source stamp, expects plain `--refresh` to update it to the source bytes and a follow-up run to exit 0 [class: REPOSITORY_TEST]
- [x] `test_newer_destination_preserved`; given a destination whose `metadata.version` frontmatter stamp is higher than the source stamp, expects classification NEWER, exit 1, and destination bytes unchanged without `--downgrade` [class: REPOSITORY_TEST]
- [x] `test_downgrade_requires_flag`; given the same newer destination with `--refresh --downgrade`, expects the destination updated to the source bytes [class: REPOSITORY_TEST]
- [x] `test_refresh_removes_extraneous_files`; given a destination carrying one file absent from the source, expects the consented refresh to remove it and a second run to exit 0 with classification CURRENT [class: REPOSITORY_TEST]
- [x] `test_refresh_is_idempotent`; given one stale destination after a consented refresh run, expects a second run to exit 0 with every destination CURRENT or SKIP [class: REPOSITORY_TEST]
- [x] `test_symlink_alias_reported_once`; given two destination roots where one is a symlink to the other and the physical copy's content drifts from the source, expects exactly one report row naming both alias paths with classification STALE and exit 1 [class: REPOSITORY_TEST]
- [x] `test_destination_resolving_to_source_skipped`; given a destination that is a symlink to the source tree, expects classification SKIP and no write [class: REPOSITORY_TEST]
- [x] `test_current_destination_exit_zero`; given a destination identical to the source, expects exit 0 and classification CURRENT [class: REPOSITORY_TEST]
- [x] `test_usage_error_exit_two`; given a missing required `--skill` argument, expects exit 2 and a usage message [class: REPOSITORY_TEST]
- [x] `test_json_report_shape`; given `--json`, expects the output to parse as JSON and carry per-destination classification fields [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 -m pytest scripts/test_skill_distribution_check.py -q` [class: REPOSITORY_TEST]
- [x] Commit: `scripts: add skill distribution integrity check` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Final validation sweep

Files: none new

- [x] Run the complete Validation Commands block → expect every gate GREEN; record any failure as a blocking defect before done [class: REPOSITORY_TEST]
- [x] Verify `git log --name-only` over the tasks' commits contains only Review Scope explicit must-fix paths and plan-related-extension files [class: REPOSITORY_TEST]
- [x] Commit (only if earlier tasks left unstaged plan-owned corrections): `skills: final validation sweep for skill reliability and portability` [class: IMPLEMENTATION_REQUIRED]
