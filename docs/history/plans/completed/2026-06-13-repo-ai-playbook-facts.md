# Plan: Repo `.ai-playbook/facts.md` — Unified Agent Facts Tier

Plan review: `docs/reviews/2026-06-13-plan-review-repo-ai-playbook-facts-r9.md` (r9, ready) · prior: r8

## Terms

- **`bootstrap-ai-playbook` skill** (renamed from `resolve-vars`): bootstraps the gitignored repo agent runtime directory on a target project — gitignore gate, path discovery, `.ai-playbook/facts.md` creation/refresh. Runs once per project when missing/stale, not every session. Name matches the artifact dir (`.ai-playbook/`) and the three-tier facts pattern (user / ownership / repo).
- **Skill spec (committed)**: `bootstrap-ai-playbook/SKILL.md` and related skill edits in the **instructions repo** — version-controlled workflow rules. Not written into target projects by bootstrap.
- **Skill invocation artifacts (gitignored)**: everything bootstrap **creates or updates on a target project** lives under `<repo>/.ai-playbook/` only. No committed runtime copies or `*.example` files for bootstrap output.
- **Repo agent runtime dir**: `<repo>/.ai-playbook/` — **always gitignored** (whole directory). Repo `.gitignore` (recommended) or local git exclude when `.gitignore` cannot be committed.
- **Repo agent facts**: `<repo>/.ai-playbook/facts.md` — bootstrap-created; fenced TOML path keys plus agent context. Shape defined inline in `bootstrap-ai-playbook/SKILL.md`.
- **Required TOML keys**: `plans_dir`, `reviews_dir`, `tmp_dir`, `facts_path`, `bootstrap_version` — bootstrap treats absence as "keys incomplete".
- **Human-canonical claims**: durable claims for human PR review belong in Layer 2 `docs/architecture/*.md`. Step 5b promotes legacy FACT bodies there; `.ai-playbook/facts.md` keeps index stubs only.
- **Session vs project bootstrap:** `using-skills` Step 0 may run every session to **read** `.ai-playbook/facts.md` and check Terms triggers; **`bootstrap-ai-playbook` executes only when triggers fire** (missing file, invalid TOML, incomplete keys, `.ai-playbook/` not gitignored, stale cached dirs). A fresh file is a no-op. Not "bootstrap every session."

## Gist & Examples

Doc-consumer skills invoke `resolve-vars` every session today (legacy name). After this plan, `bootstrap-ai-playbook` runs **once per target project**, writing artifacts only into gitignored `.ai-playbook/`.

**Two layers (do not conflate):**

| Layer | Location | Committed? |
|-------|----------|------------|
| Skill instructions | `agents/skills/bootstrap-ai-playbook/SKILL.md` (instructions repo) | Yes |
| Bootstrap output | `<target-repo>/.ai-playbook/*` | No — always gitignored |

**Shape of `facts.md`** (inline in skill spec; example values come from **on-disk discovery**, not copied from this plan):

````markdown
```toml
plans_dir = "docs/plans/"              # instructions repo: discovered on disk
reviews_dir = "docs/reviews/"
tmp_dir = "docs/tmp/"
facts_path = ".ai-playbook/facts.md"
bootstrap_version = "1"
```

## Related Jira tasks
...
````

**Bootstrap gitignore prompt:** repo `.gitignore` vs local exclude — no write until `git check-ignore -q .ai-playbook/facts.md` passes.

## Evaluation Criteria

**Quality dimensions:**
- **Artifact placement**: bootstrap writes only under target `.ai-playbook/`; no committed runtime templates.
- **Gitignore invariant**: entire `.ai-playbook/` ignored before any bootstrap write.
- **Task order**: no bootstrap before Task 3 merge (legacy `resolve-vars` must not run on target repos).
- **Correctness**: path keys from on-disk discovery; consumers read `.ai-playbook/facts.md`; no per-session bootstrap wording after Task 7; **zero** `resolve-vars` references in consumer skills (broad grep gate; `bootstrap-ai-playbook/SKILL.md` excluded — may note rename once in its own body).

**Release gates:**
- Full Validation Commands pass after Task 7.
- `verify-doc-hierarchy.sh self-test` and `stale-bootstrap-test` pass.
- Instructions repo: post-Task 3 bootstrap `plans_dir` matches existing `docs/plans/` layout.

## Review Scope

**Production code — in scope:**
- `agents/skills/bootstrap-ai-playbook/SKILL.md` *(rename from `resolve-vars/`)*
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/learn/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/receiving-code-review/SKILL.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/how-to-write-skills/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/doc-hierarchy/company-decisions.md`
- `agents/skills/doc-hierarchy/migration-map.md`
- `agents/skills/doc-hierarchy/instruction-templates.md`
- `agents/skills/doc-hierarchy-migrate/SKILL.md`
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`
- `agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `docs/AGENTS.md`
- `README.md`
- `.gitignore`

**New files:** `docs/plans/2026-06-13-repo-ai-playbook-facts.md` only

**Out of scope — reject review findings:**
- Committed `repo-facts.md.example`, `docs/templates/*`, or other committed bootstrap output copies
- `~/.ai-playbook/facts.md`, `~/.cursor/rules/load-facts-at-task-start.mdc` (Task 1 user-local)
- Company repo Step 5b pilots

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

git check-ignore -q .ai-playbook/facts.md; test $? -eq 0
git check-ignore -q .ai-playbook/; test $? -eq 0
! git ls-files --error-unmatch .ai-playbook/ 2>/dev/null

! test -f docs/facts.md.example
! test -f docs/templates/repo-facts.md.example
test ! -e docs/facts.md
! git ls-files --error-unmatch docs/facts.md 2>/dev/null

# Post-bootstrap path sanity (instructions repo)
rg -q '^plans_dir = "docs/plans/"' .ai-playbook/facts.md

# Zero legacy resolve-vars in consumer skills (Related links, integration tables, invoke wording — all forms)
# bootstrap-ai-playbook/SKILL.md excluded (may document "renamed from resolve-vars" in its own body)
! rg -q 'resolve-vars' agents/skills/ --glob 'SKILL.md' --glob '!**/bootstrap-ai-playbook/**'

# No per-session bootstrap wording (run AFTER Task 7)
rg -n 'invoke.*bootstrap-ai-playbook|At (task start|Phase 0).*bootstrap-ai-playbook|once per session.*bootstrap|per-session bootstrap' \
  agents/skills/ docs/ README.md projects/.ai-playbook/ --glob 'SKILL.md' --glob '!bootstrap-ai-playbook/**'

rg -n 'docs/maintenance/facts\.md' \
  agents/skills/doc-hierarchy/instruction-templates.md agents/skills/doc-hierarchy/migration-map.md agents/skills/doc-hierarchy/SKILL.md

rg -n 'facts\.md\.example' README.md docs/AGENTS.md projects/.ai-playbook/agent-runtime-layout.md

agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh self-test
agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh stale-bootstrap-test

test -L claude/skills && [ "$(readlink claude/skills)" = "../agents/skills" ]
```

### Task 1: User facts + remove legacy committed facts example

Files:
- `docs/facts.md.example` *(delete)*
- `~/.ai-playbook/facts.md` *(user-local)*
- `~/.cursor/rules/load-facts-at-task-start.mdc` *(user-local)*

- [x] Update `repo_facts_rel` in `~/.ai-playbook/facts.md` to `.ai-playbook/facts.md`
- [x] `git rm docs/facts.md.example`; grep repo for references; point to `bootstrap-ai-playbook` skill for format (no replacement example file)
- [x] Update `load-facts-at-task-start.mdc`: load via `repo_facts_rel` key; bootstrap owner is `using-skills` → `bootstrap-ai-playbook` (read-only load here)
- [x] Commit: `facts: repo agent artifacts under gitignored .ai-playbook/`

### Task 2: Gitignore `.ai-playbook/` only (no bootstrap yet)

Files:
- `.gitignore`

- [x] Add `.ai-playbook/` to `.gitignore`; remove `/docs/facts.md` entry
- [x] Replace `.gitignore` comment: repo agent runtime dir (bootstrap output; see `bootstrap-ai-playbook` skill)
- [x] If local untracked `docs/facts.md` exists: hand-move content into `.ai-playbook/facts.md` manually (do **not** invoke bootstrap — legacy `resolve-vars` skill still active until Task 3)
- [x] **Hard gate:** do not invoke `bootstrap-ai-playbook` until Task 3 is merged
- [x] Commit: `.gitignore: gitignore entire .ai-playbook/`

### Task 3: Rename `resolve-vars` → `bootstrap-ai-playbook` and rewrite skill

Files:
- `agents/skills/resolve-vars/` → `agents/skills/bootstrap-ai-playbook/` *(git mv)*
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `.ai-playbook/facts.md` *(gitignored — created at end of task)*

- [x] `git mv agents/skills/resolve-vars agents/skills/bootstrap-ai-playbook`; update frontmatter `name:` and description; grep **all** stale `resolve-vars` strings in `agents/skills/` (invoke wording, `` the `resolve-vars` skill ``, `` | `resolve-vars` | `` table cells, Related markdown links, Integration Points); expect **zero** matches outside `bootstrap-ai-playbook/SKILL.md` after this task
- [x] Document two-layer model in skill body: skill spec committed; **all invocation artifacts** under target `.ai-playbook/` only
- [x] Remove `docs/facts.md` / `docs/maintenance/facts.md` from fallbacks, default map, and "create docs/facts.md" rules
- [x] Define inline shape: fenced TOML block (required keys incl. `bootstrap_version`) + prose below; parse only opening fence; re-read-before-write
- [x] Path-key generation: **on-disk discovery first** (prefer shallowest existing dir); never seed from plan/doc-hierarchy literals without verification
- [x] Gitignore gate: ask repo `.gitignore` vs local exclude; block writes until `.ai-playbook/` ignored
- [x] Hard-fail when `git ls-files docs/maintenance/facts.md` → redirect to doc-hierarchy-migrate Step 5b
- [x] **After skill rewrite:** run bootstrap on instructions repo; verify `plans_dir = "docs/plans/"`, `reviews_dir = "docs/reviews/"`, `tmp_dir = "docs/tmp/"`
- [x] Commit: `bootstrap-ai-playbook: bootstrap writes only to target .ai-playbook/` (not `.ai-playbook/facts.md`)

### Task 4: Doc-consumer skills + docs-branch + using-skills

Files:
- 12 consumer `SKILL.md` files (Review Scope list)
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`

- [x] **`using-skills`:** Step 0 reads `.ai-playbook/facts.md` each session; invokes `bootstrap-ai-playbook` **only when Terms triggers fire** (at most one bootstrap call per session; skill no-ops when file is fresh). Remove per-session `resolve-vars` from principles L39–40
- [x] Other consumers: read TOML keys from `.ai-playbook/facts.md`; do not invoke `bootstrap-ai-playbook` each task (reference `using-skills`)
- [x] **`doing-code-review`:** L244 forbidden list includes `.ai-playbook/facts.md`; L248–252 quick-scan greps `.ai-playbook/facts`; remove legacy committed facts paths
- [x] **`docs-branch`:** add `.ai-playbook/` to `SHADOW_CANDIDATES`; extend orphan-branch strip regex; run `public_hygiene_scan_script` (or `rg -f` patterns file) on `.ai-playbook/facts.md` before any force-add — **abort sync on non-zero**; reconcile exclude-only guidance with mandatory repo gitignore default
- [x] Commit: `skills: gitignored .ai-playbook/ read path; bootstrap via using-skills`

### Task 5: Doc-hierarchy family + verify script

Files:
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/doc-hierarchy/company-decisions.md`
- `agents/skills/doc-hierarchy/migration-map.md`
- `agents/skills/doc-hierarchy/instruction-templates.md`
- `agents/skills/doc-hierarchy-migrate/SKILL.md`
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`
- `agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh`

- [x] **`doc-hierarchy/SKILL.md`:** migration-complete signal #2 → `repo_facts_rel` / `.ai-playbook/facts.md`; Precedence L34 and L89 — remove per-session `resolve-vars`; consumers read `.ai-playbook/facts.md`, bootstrap via `using-skills` when triggers fire
- [x] **`instruction-templates.md` + `migration-map.md` + `company-decisions.md`:** remove committed `maintenance/facts.md` as repo facts home; document gitignored `.ai-playbook/` runtime
- [x] **`doc-hierarchy-migrate/SKILL.md` + `doc-hierarchy-upkeep/SKILL.md`:** rewrite Integration Points / Related tables (`| resolve-vars |`, `` the `resolve-vars` skill ``) → `bootstrap-ai-playbook`; `{tmp_dir}` from `.ai-playbook/facts.md` TOML when bootstrapped (not invoke resolve-vars)
- [x] **`doc-hierarchy-migrate/SKILL.md` Step 5b:** insert before Step 5 gate (promote FACTs → Layer 2; index stubs in `.ai-playbook/facts.md`; gitignore `.ai-playbook/`; `git rm` legacy committed facts)
- [x] **`doc-hierarchy-upkeep`:** FACT/Jira updates to `.ai-playbook/facts.md`; paired Layer 2 update for human-canonical claims; re-read-before-write
- [x] **`verify-doc-hierarchy.sh`:** update instructions-repo guard L38–42 from `resolve-vars/SKILL.md` to `bootstrap-ai-playbook/SKILL.md`; self-test asserts guard fatals when `REPO_ROOT` is skill install tree; `gate_step5` greps `.ai-playbook/facts.md` + gitignore `.ai-playbook/`; update `bootstrap_fixture_expected_mini` and self-test fixtures; add **negative** fixture for committed `docs/maintenance/facts.md`
- [x] Implement **`stale-bootstrap-test`** subcommand: register in script `case`; TOML refresh with prose preserved; inline-code-fence edge case in fixture
- [x] Document `stale-bootstrap-test` invocation in `doc-hierarchy-migrate/SKILL.md`
- [x] Commit: `doc-hierarchy: gitignored .ai-playbook/ + verify gates`

### Task 6: Instructions repo docs

Files:
- `docs/AGENTS.md`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `README.md`

- [x] **`docs/AGENTS.md`:** hierarchy table → `.ai-playbook/facts.md`; Jira ledger target; remove `docs/facts.md.example` from L3 key-names pointer; temporary artifacts read paths from repo agent facts
- [x] **`agent-runtime-layout.md`:** Facts files section → three-tier `.ai-playbook/`; Path discovery L24 bootstrap-only (not per-session); remove L66/L135 `docs/facts.md.example` bullets
- [x] **`README.md`:** layout tree — remove `facts.md.example`; catalog rows for `bootstrap-ai-playbook`, `execute-plan`, `doc-hierarchy` (read `.ai-playbook/facts.md`)
- [x] Commit: `docs: gitignored .ai-playbook/ agent tier`

### Task 7: Doc closure and release gates

- [x] Grep stale `facts.md.example`, `docs/maintenance/facts.md` as `repo_facts_rel`, per-session bootstrap in `README.md` / `projects/.ai-playbook/`
- [x] Confirm zero-match `resolve-vars` gate passes (`! rg -q 'resolve-vars' agents/skills/ ... --glob '!bootstrap-ai-playbook/**'`)
- [x] Run **full Validation Commands** block
- [x] Update plan header: latest review ready reference
- [ ] Commit: `docs: close repo agent facts references`

## Monitor

| Item | Owner | Notes |
|------|-------|-------|
| Task 1 user-local steps | Task 1 checklist | Out of repo diff; verify manually before Task 4 |
| Company Step 5b pilot | Follow-up execute-plan | After skill merge |
| Concurrent FACT edits | doc-hierarchy-upkeep | Re-read-before-write |
| TOML fence vs prose code fences | stale-bootstrap-test fixture | Task 5 |
