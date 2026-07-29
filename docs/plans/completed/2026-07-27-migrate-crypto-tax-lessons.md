# Plan: Migrate crypto-tax lessons out of the playbook corpus

Follow-up: fixes the `learn` skill root cause so project-specific lessons stop landing in the generic UL corpus.

## Terms

- **UL corpus**: `ai-playbook/projects/.ai-playbook/development_lessons.md`, the user-level cross-project lessons file (strict `UL#N` namespace, resolves via the `shared_docs_dir` symlink to `~/Projects/.ai-playbook/development_lessons.md`). Gate-validated read-only by `lessons_index.py`.
- **Project corpus**: a repo's own `docs/maintenance/development_lessons.md` (convention `#N` namespace). Tax-reporting's lives at `<project-repo>/docs/maintenance/development_lessons.md` (76 lessons, contiguous, tracked). The playbook repo has none.
- **MOVE lesson**: a playbook lesson whose rule AND example are crypto-tax-domain (FIFO lot matching, OGR authority, dust partitioning, Koinly CSV, reward TAXABLE_NOW/DEFERRED_BY_LAW classification, Portugal tax rules, wallet-kind classification). Target: tax-reporting corpus.
- **STAY+GENERALIZE lesson**: a playbook lesson whose rule is portable but whose only example is crypto-tax. Stays in the playbook; its Example paragraph is rewritten to a non-crypto analog.
- **Duplicate**: a MOVE lesson that near-duplicates an existing tax-reporting lesson (e.g. playbook #54 OGR authority ≈ tax #42). Merged: keep the richer, fold the other's unique insight in as a witness, drop the dup.

## Gist & Examples

The playbook's UL corpus (207 lessons) is the cross-project lessons file referenced from user-level instructions. Roughly 70-75 of those lessons are crypto-tax-domain: they teach rules that only make sense inside the tax-reporting codebase (FIFO lot matching, OGR directional authority, Koinly CSV column alignment, reward classification, Portugal Anexo J mechanics). They landed there because the `learn` skill's cross-project-vs-project-specific decision is judgment-only with no incident-repo-vs-cwd check, and the playbook repo has no project corpus of its own, so any lesson captured while cwd is the playbook repo defaults into the UL file.

Example of the contamination: playbook lesson #54 ("OGR Directional Authority vs Wholesale Replacement") is fundamentally about the tax-reporting OGR report's relationship to FIFO aggregation. Its rule, its example, and its `CRG-017` cross-reference are all crypto-tax-domain. It belongs in tax-reporting's corpus (which already has a near-duplicate, tax lesson #42). Same for playbook #33 (Koinly TH CSV column alignment ≈ tax #10), #52 (OGR overrides must precede aggregation), #76 (FIFO count-matched-items safety), etc.

The fix has two halves:

1. **Migrate** the ~70-75 crypto-tax-domain lessons from the playbook UL corpus into the tax-reporting project corpus, merging duplicates with the richer version. Generalize the ~14 truly-portable borderline lessons (keep their rules, rewrite their crypto examples to non-crypto analogs). Renumber both corpora to stay contiguous. Repoint every cross-reference (intra-corpus `#N`, the one cross-repo cite, instruction-file links).
2. **Prevent recurrence** by fixing the `learn` skill: add an incident-repo-vs-cwd check, a residual-domain test, and a project-corpus existence check, so a project-specific lesson learned while cwd is the playbook repo is deferred to the incident repo's corpus instead of defaulting into the UL file.

Examples of the desired end state:
- Playbook UL corpus: ~135 lessons (the 122 CROSS + ~14 generalized borderline), zero crypto-tax-domain fingerprints (no `CryptoTaxReport`, no `crypto_reporting.py`, no `Koinly`, no `CRG-NNN`, no `docs/history/plans/2026-06-*` paths). Mainstream tokens (BTC/ETH/EUR/USD) kept only where they are genuine analogs inside a portable rule; domain tickers like `OSBGT` move WITH their lesson or get generalized.
- Tax-reporting corpus: ~75-140 lessons depending on merge outcomes (76 existing + ~60 net new after dedup), contiguous, convention-tagged.
- `learn` skill: a fresh run from the playbook repo capturing a tax-reporting incident either refuses to write to the UL corpus or routes the lesson to tax-reporting's corpus.

## Evaluation Criteria

**Quality dimensions:**
- Portability: every lesson remaining in the playbook UL corpus reads naturally to an engineer who has never seen the tax-reporting codebase; no lesson's rule depends on crypto-tax domain knowledge.
- Completeness: every MOVE lesson's rule is preserved in tax-reporting (no rule lost in transit); merges preserve BOTH lessons' rules when they differ (complementary lessons are NOT merged; see duplicate-merge procedure).
- Reference integrity: zero dangling `#N` cites in either corpus or either repo's instruction files; the one known cross-repo cite (tax #42 `user-level #54`) is repointed. Cite-format aware: tax AGENTS.md cites are backtick-quoted (`` `development_lessons.md` #N ``), not bare `path #N`.
- Prevention: the `learn` skill fix is enforceable: at least one of the three checks (the project-corpus existence check) is a mechanical fail-loud gate, not pure LLM judgment; the other two are reinforced by a post-hoc audit step.
- Contiguity: both corpora are contiguous `## 1..N` after the migration (no gaps AND no duplicates; contiguity checks must test both).

**Release gates:**
- `lessons_index.py ~/Projects/.ai-playbook/development_lessons.md` exits 0 (UL tag invariant + contiguity).
- Tax-reporting corpus contiguity check (`grep '^## [0-9]' | sort -n`) passes; Family tags present where the convention expects them.
- Zero crypto-tax-domain fingerprints in the playbook UL corpus (grep for `CryptoTaxReport|CryptoCapitalGainEntry|crypto_reporting\.py:[0-9]|CRG-[0-9]{3}|docs/history/plans/2026-0[567]-` excluding the playbook's own `2026-07-27-*` plans returns no matches).
- Both repos' instruction files (`ai-playbook/docs/AGENTS.md`, `tax-reporting/AGENTS.md` + `CLAUDE.md` symlinks): zero dangling `#N` cites.
- `learn` skill updated in `~/.agents/skills/learn/SKILL.md` (the playbook's `agents/skills/learn/` is a symlink to it, one file, same inode).
- Public hygiene scan passes on changed files in both repos.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Playbook repo:**
- `projects/.ai-playbook/development_lessons.md` (the UL corpus: remove MOVE lessons, generalize borderline, renumber, fix cross-refs)
- `agents/skills/learn/SKILL.md` (the vendored learn skill copy: add the three preventive checks)
- `docs/plans/2026-07-27-migrate-crypto-tax-lessons.md` (this plan; archive on completion)
- `docs/AGENTS.md` (verify no dangling corpus cites after the move; update the corpus-topology prose if the UL corpus's role description changed)

**Tax-reporting repo:**
- `docs/maintenance/development_lessons.md` (the project corpus: receive/merge MOVE lessons, renumber, fix the one cross-repo cite)
- `AGENTS.md` (and the `CLAUDE.md` symlink): renumber any `development_lessons.md #N` cites whose target shifted due to merges

**Runtime skill source (the playbook repo's `agents/skills/learn/` symlinks here, one file):**
- `~/.agents/skills/learn/SKILL.md` (the single source the agent loads at runtime; the playbook repo's `agents/skills/learn/SKILL.md` resolves to this same inode)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a migration task, fixes a regression introduced by the move, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- The 12 pre-existing unpushed commits on the playbook branch (the five-worker panel work); they are squashed at push time but their content is not edited by this migration.
- The ~63 crypto-tax fingerprints already public on `ai-playbook`'s `origin/main` from older commits; this migration fixes the local state and the force-push replaces origin, but does not separately scrub origin's pre-migration history beyond what the squash + force-push accomplishes.
- Extending the skill-gate hook (`skill_gate.py`) to cover the UL corpus (diagnostic option D); deferred to a follow-up if the Step 1.2/1.7/2 fix proves insufficient.
- tax-reporting's push to its own origin (separate repo, separate decision; the migration commits land locally and you confirm the push separately).

## Validation Commands

```bash
# Playbook UL corpus: tag invariant + contiguity gate
python3 ~/.ai-playbook/scripts/lessons_index.py ~/Projects/.ai-playbook/development_lessons.md
# Expect: exit 0, "unclassified: 0"

# Playbook UL corpus: zero crypto-tax-domain fingerprints remain (mainstream tickers/fiat allowed ONLY in genuinely-portable lessons, not inside MOVE candidates)
# Category 1: real production class/dataclass/enum/function/test names
! rg -n 'CryptoTaxReport|CryptoCapitalGainEntry|CryptoRewardIncomeEntry|RewardTaxClassification|_classify_reward_tax_status|_partition_taxable_now|_aggregate_capital_entries|_re_evaluate_aggregated_review|_write_dust_summary_block|_parse_capital_gains_file|TestCryptoSupplementarySheet|popular_crypto_tokens\.json' \
  projects/.ai-playbook/development_lessons.md
# Category 2: real source file paths (with OR without line numbers) + module paths
! rg -n 'crypto_reporting\.py|koinly_parser\.py|src/tax_reporting|crypto_rules\.md|crypto_reporting_guidelines\.md' \
  projects/.ai-playbook/development_lessons.md
# Category 3: tax-domain doc codes + PT tax-specific terms + domain service/locale names
! rg -n 'CRG-[0-9]{3}|PT-C-[0-9]{3}|Anexo [A-Z]|Quadro [0-9]|Autoridade Tribut|Koinly|Portugal' \
  projects/.ai-playbook/development_lessons.md
# Category 4: internal plan/feature-notes paths with dates (excluding the playbook's own 2026-07-27 plans)
! rg -n 'docs/history/(plans|feature-notes)/2026-0[567]-' \
  projects/.ai-playbook/development_lessons.md | grep -v '2026-07-27-five-worker\|2026-07-27-phase-2\|2026-07-27-migrate'
# Category 5: domain framing terms that survive even after identifier redaction
# (judgment-flagged, not hard-fail: review any remaining hits to confirm the lesson is genuinely portable)
rg -n '\bOSBGT\b|\bFIFO\b|\bOGR\b|\bdust[- ]partition\b|taxable_now|deferred_by_law' \
  projects/.ai-playbook/development_lessons.md || echo "(no domain-framing terms; clean)"

# Playbook UL corpus contiguity (1..M, no gaps AND no duplicates)
python3 -c "
import re,sys
nums=sorted(int(m.group(1)) for m in re.finditer(r'^## (\d+)\.', open('projects/.ai-playbook/development_lessons.md').read(), re.M))
assert nums==list(range(1,len(nums)+1)), f'contiguity broken: {nums[:5]}...{nums[-5:]}' or len(set(nums))!=len(nums)
print(f'contiguity OK: 1..{len(nums)}')
"

# Tax-reporting corpus contiguity (1..N, no gaps AND no duplicates)
cd <project-repo>
python3 -c "
import re
nums=sorted(int(m.group(1)) for m in re.finditer(r'^## (\d+)\.', open('docs/maintenance/development_lessons.md').read(), re.M))
assert nums==list(range(1,len(nums)+1)), f'contiguity broken'
print(f'contiguity OK: 1..{len(nums)}')
"

# Both repos' instruction files: zero dangling #N cites (cite format is `development_lessons.md` #N, backtick-quoted)
# NOTE: use `rg -o` (default regex engine). Do NOT use `rg -E`; in ripgrep -E is --encoding, not POSIX ERE.
cd <playbook-repo>
rg -o '`development_lessons\.md` #[0-9]+' docs/AGENTS.md AGENTS.md 2>/dev/null | sed -E 's/.*#([0-9]+)/\1/' | sort -n | uniq
cd <project-repo>
rg -o '`development_lessons\.md` #[0-9]+' AGENTS.md 2>/dev/null | sed -E 's/.*#([0-9]+)/\1/' | sort -n | uniq
# Each captured N must exist as a '## N.' header in the respective corpus. Verify with:
# for n in <captured>; do grep -q "^## $n\." docs/maintenance/development_lessons.md || echo "DANGLING: #$n"; done

# learn skill fix present (agents/skills/learn/SKILL.md is a symlink to ~/.agents/skills/learn/SKILL.md; ONE file)
grep -c 'incident-repo' ~/.agents/skills/learn/SKILL.md
# Expect: >=1
stat -f '%i' <playbook-repo>/agents/skills/learn/SKILL.md ~/.agents/skills/learn/SKILL.md | uniq | wc -l
# Expect: 1 (same inode; confirms single file, no two-copy sync needed)

# Public hygiene on changed files in both repos
cd <playbook-repo>
bash scripts/scan-public-hygiene.sh --changed-from main
```

### Task 1: Build the migration manifest

Files:
- `docs/tmp/migration-manifest.md` *(new, gitignored)*

- [x] Read the playbook UL corpus and finalize the per-lesson disposition: MOVE (target tax-reporting), STAY+GENERALIZE (keep in playbook, rewrite example), or STAY AS-IS (CROSS). Use the Explore-agent classification as the starting point (41 hard CRYPTO-TAX + ~30 borderline-as-crypto = MOVE; ~14 truly-generic borderline = STAY+GENERALIZE; 122 CROSS = STAY). Verify each borderline call by reading the lesson's Rule + Example.
- [x] For each MOVE lesson, check tax-reporting's corpus for a near-duplicate (the ~15 candidate pairs flagged: playbook #54↔tax #42, #33↔#10, #18↔#31, #45↔#49, etc.). Record the duplicate mapping and decide which version is richer per pair.
- [x] Build the playbook renumber map (CROSS + STAY+GENERALIZE lessons → new contiguous 1..M).
- [x] Build the tax-reporting append/merge list (MOVE lessons → tax-corpus positions #77+, minus merges).
- [x] Build the cross-ref rewrite manifest: every playbook intra-corpus `#N` cite (843 tokens) classified as STAY-STAY (renumber), STAY-MOVED (convert to title pointer or drop), or MOVED-MOVED (drops with the lesson); the one cross-repo cite (tax #42 `user-level #54`); tax-reporting AGENTS.md cites whose target shifted.
- [x] Commit: `docs(plans): migration manifest for crypto-tax lesson move`

### Task 2: Receive/merge MOVE lessons into the tax-reporting corpus

Files:
- `<project-repo>/docs/maintenance/development_lessons.md`

**Duplicate-merge decision procedure (apply per candidate pair):**
1. **Same rule?** If both lessons teach the SAME rule (same Principle, same Rule steps), they are true duplicates → MERGE (keep the richer example/witness, fold any unique See-also from the other, drop the dup).
2. **Different rule, same topic?** If the two lessons teach DIFFERENT rules about the same topic (e.g. playbook #54 "OGR directional authority vs wholesale replacement" is Family D; tax #42 "magnitude/materiality gate belongs to one decision" is Family B, different rules), they are COMPLEMENTARY, NOT duplicates → APPEND both as separate lessons, cross-link them in See-also. Do NOT merge.
3. **Uncertain?** If you cannot confirm same-rule after reading both Rule sections, APPEND as separate lessons and cross-link. Never merge on topic-similarity alone; a merge that drops a rule is the worst outcome.

- [x] In the tax-reporting repo, hold a fresh `learn` skill-gate marker (`python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker learn ...`) to satisfy the corpus-edit gate.
- [x] For each MOVE lesson in tax-corpus order: classify its duplicate-candidate per the procedure above. MERGE only true same-rule duplicates; APPEND complementary or unique lessons as the next tax-corpus lesson. Preserve every lesson's Rule/Principle/Trigger/Shape/Why intact.
- [x] Keep tax-domain cross-references correct in their new home: `CRG-NNN`, `PT-C-NNN`, `crypto_reporting_guidelines.md`, `docs/history/plans/2026-06-*`, `docs/maintenance/glossary.md` cites move WITH the lesson (tax-reporting has these docs). Keep `coding_guidelines.md #N` and `agent_workflow_guidelines.md #N` cites (resolve via shared_docs_dir from tax-reporting).
- [x] Renumber tax corpus to contiguous 1..N (compaction only if true-same-rule merges removed slots; complementary appends never remove a slot).
- [x] Repoint the one cross-repo cite: tax lesson #42's `user-level #54` → the new tax-corpus number for the OGR-authority lesson (whichever of #54 or its complement that became). If #54 and #42 were complementary (likely, per the decision procedure), both exist in tax-reporting now and the cite points to #54's new number.
- [x] Run → expect GREEN: tax corpus contiguity check (Python contiguity script from `## Validation Commands`) passes, both no-gaps AND no-duplicates.
- [x] Commit (in tax-reporting repo): `lessons: import crypto-tax lessons from playbook UL corpus`

### Task 3: Remove MOVE lessons, generalize borderline, renumber the playbook UL corpus

Files:
- `projects/.ai-playbook/development_lessons.md`

- [x] Remove every MOVE lesson (per the manifest).
- [x] Generalize each STAY+GENERALIZE lesson: rewrite its Example paragraph to a non-crypto analog (the Rule/Principle/Trigger/Shape stay). Keep mainstream tokens (BTC/ETH/EUR/USD) only where they are genuine analogs inside a portable rule; treat `OSBGT` as a domain ticker (generalize it to a role like `an unpriced staking token` or move the lesson). Replace crypto-tax-specific scaffolding (real class names, real file paths with line numbers, real plan slugs with dates) with generic roles.
- [x] Renumber to contiguous 1..M using the `lessons_migrate.py` renumber engine (or its semantics) scoped to the playbook UL corpus.
- [x] Rewrite intra-corpus `#N` cites per the manifest (STAY-STAY renumber; STAY-MOVED convert to title pointer or drop).
- [x] Run → expect GREEN: `python3 ~/.ai-playbook/scripts/lessons_index.py ~/Projects/.ai-playbook/development_lessons.md` exits 0.
- [x] Run → expect GREEN: the fingerprint greps in `## Validation Commands` return no matches.
- [x] Commit: `lessons(ul): move crypto-tax lessons to tax-reporting; generalize borderline examples`

### Task 4: Fix the `learn` skill (root-cause prevention)

Files:
- `~/.agents/skills/learn/SKILL.md`: the runtime source. NOTE: `~/.agents/skills` is a symlink to the playbook repo's `agents/skills/`, so `~/.agents/skills/learn/SKILL.md` and `agents/skills/learn/SKILL.md` are the SAME inode (one tracked file). Editing either is sufficient; do NOT treat them as separate copies to sync.

- [x] Step 1.2 item 4: add the incident-repo-vs-cwd pre-check before the three-way fork. "Before classifying as fork (2) cross-project: identify the repo where the incident occurred (the witness's repo, from file paths / git history / session context). If that repo is not the current cwd repo, you are capturing a deferred lesson: STOP and either (a) `cd` to the incident repo and re-run `learn` there, or (b) ask the user whether to defer. Never write a project-specific incident into the UL corpus just because that is the corpus available in the current cwd."
- [x] Step 1.7: add a post-redaction residual-domain test (new step 6). "After redaction, run the residual-domain test: does the rule still require a specific application domain (tax reporting, capital-gains calculation, batch-row aggregation) to be meaningful? If yes, even with all proper nouns redacted, the lesson is fork (3) project-specific. Route it to the incident repo's project corpus."
- [x] Step 2: add a **mechanical** project-corpus existence check (this is the enforceable gate, not pure judgment). "If the chosen scope is fork (3) project-specific, verify `$REPO/docs/maintenance/development_lessons.md` exists (resolved from `project_guidelines_rel` in repo facts) BEFORE any corpus write. If it does NOT exist, the placement FAILS LOUD: do not silently fall back to the UL corpus. Either bootstrap the project corpus, switch to the incident repo, or escalate to the user. Note: the playbook repo (`skills_repo_path` / `instructions_repo`) has no `project_guidelines_rel` and no project corpus, so any fork-3 lesson learned while cwd is the playbook repo MUST fail-loud and be deferred to the incident repo." This check is mechanical (a filesystem/facts lookup), not LLM judgment, and is the backstop that makes the fix enforceable even if the Step 1.2/1.7 judgment checks are missed.
- [x] Completion Checklist: add "incident-repo == cwd-repo verified for every UL#N capture, or deferred capture was routed to the incident repo's project corpus; AND the fork-3 project-corpus existence check ran for every project-specific candidate".
- [x] Run → expect GREEN: `grep -c 'incident-repo\|project-corpus existence' ~/.agents/skills/learn/SKILL.md` returns >=1. Confirm the playbook symlink resolves to the same inode (`stat -f '%i' agents/skills/learn/SKILL.md ~/.agents/skills/learn/SKILL.md | uniq | wc -l` == 1).
- [x] Commit: `learn: prevent project-specific lessons from landing in the UL corpus`

### Task 5: Update instruction-file references and verify integrity

Files:
- `docs/AGENTS.md` (playbook; verify + update corpus-topology prose if the UL corpus role changed)
- `<project-repo>/AGENTS.md` (renumber shifted cites)

- [x] Playbook `docs/AGENTS.md`: verify the corpus-topology prose still describes the UL corpus correctly after the move; update if the description referenced crypto-tax content that is now gone.
- [x] Tax-reporting `AGENTS.md` (and `CLAUDE.md` symlink): for each `development_lessons.md #N` cite whose target shifted due to Task 2 merges/renumber, rewrite to the new number.
- [x] Grep both repos' instruction files + corpora for any `#N` that no longer resolves to a `## N.` header; fix or drop each dangling cite.
- [x] Run → expect GREEN: both instruction-file cite checks in `## Validation Commands` (every captured N resolves to a header).
- [x] Commit (playbook): `docs: update corpus references after crypto-tax lesson migration`
- [x] Commit (tax-reporting, if AGENTS.md cites shifted): `docs: renumber development_lessons cites after import`

### Task 6: Squash + force-push playbook; commit tax-reporting locally

Files:
- (git operations; no file edits)

**Ordering + rollback (two-repo safety):**
- Task 2 (tax-reporting receives) MUST complete and commit BEFORE Task 3 (playbook removes). This guarantees no lesson is ever in neither corpus. If Task 3 fails mid-way, the playbook's pre-Task-3 state still has all lessons (recoverable via `git checkout`); tax-reporting's Task-2 commit is correct and independent (it added lessons; it does not need rollback if the playbook side fails).
- If Task 2 fails mid-way: `git checkout -- docs/maintenance/development_lessons.md` in tax-reporting to revert; the playbook is untouched.
- The force-push (this task) happens ONLY after both corpora validate (Tasks 2-5 GREEN). Before the force-push, the playbook's pre-migration state is recoverable from the reflog / the branch tip before squashing.
- Snapshot both corpus files to `{tmp_dir}` before Task 2 and Task 3 as a belt-and-suspenders backup: `cp projects/.ai-playbook/development_lessons.md docs/tmp/ul-corpus-backup.md` (playbook) and equivalent in tax-reporting.

- [x] Snapshot both corpus files to `{tmp_dir}` as backups before proceeding (belt-and-suspenders).
- [x] Confirm Task 2 (tax-reporting receive) committed BEFORE Task 3 (playbook remove) started: verify tax-reporting has the import commit and playbook removal has not begun, OR both are complete.
- [ ] Playbook: squash the 12 pre-existing local commits + Tasks 1-5 commits into a coherent set (e.g. one for the five-worker panel work, one for the lessons migration + learn fix). Confirm the squashed history reads cleanly. **DEFERRED to post-Phase-3** (avoid double force-push if review finds fixes).
- [ ] Playbook: force-push to `origin/main` (history rewrite approved; repo has few users). Note the pre-push branch tip for reflog recovery. **DEFERRED to post-Phase-3** (await explicit push confirmation).
- [ ] Playbook: post-push verification: UL corpus fingerprint greps clean; `lessons_index.py` green; instruction cites resolve. **DEFERRED with the push.**
- [x] Tax-reporting: confirm the import commit is local on its current branch; surface to user for the separate push decision. Tax-reporting's default branch is `master` (not `main`); confirm the branch and push target with the user before any push. Do not push tax-reporting without explicit confirmation.
- [ ] Run → expect GREEN: the full `## Validation Commands` block from the playbook repo. **(run in Phase 2 below)**
- [x] Commit: (no new commit; this task is the squash + push itself)
