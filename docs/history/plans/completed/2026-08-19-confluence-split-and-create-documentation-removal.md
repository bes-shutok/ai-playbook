# Plan: Confluence skill split and create-documentation layer removal

Requirements buffer: `docs/tmp/plan-requirements-confluence-page-sync-split.md`.
Branch: `2026-08-19-confluence-page-sync-split` (user confirmed; push stays off).

## Terms

- **confluence-page-sync**: new skill owning Confluence page publishing and synchronization: full-body page updates, parent/child page creation, stored-HTML inspection, Mermaid diagram integrity (preservation and duplicate detection), Confluence version and local revision ledgers, post-publish verification.
- **tdd-design**: new skill generating Technical Design Documents, promoted from `create-documentation/create-tdd.md`. Distinct from `tdd-guide`, which owns Kent Beck test-driven development methodology.
- **Sync manifest / ledger**: repository-side record of Confluence `version.number`, last-modified timestamp, source revision, and sync status; existing convention `docs/maintenance/confluence-sync-manifest.json`, validated by `scripts/confluence-mirror-hygiene.sh`.
- **Single-rendering pair**: a Mermaid fenced source block plus exactly one rendering representation (native fenced-block render, extension node, or image embed) on the published page; the duplicate-detection gate asserts one representation per intended diagram.
- **Review staging**: review artifact under `{reviews_dir}` plus `.stats.json` sidecar per the `review-staging` skill; consumed unchanged by `review-confluence-doc`.
- **Skill-gate marker (plans class; Session key)**: before EVERY Write/Edit of a plan file (create, update, completion), refresh the per-(project, session) marker by running, in order:
  ```bash
  mkdir -p "$HOME/.ai-playbook/runtime/skill-invoked"   # mode 0o700
  SID="$(python3 "$HOME/.ai-playbook/scripts/session_channel.py")"
  # If SID is empty after strip: omit --session-id entirely (core keys literal "no-session").
  # Otherwise pass it verbatim. The helper prints CLAUDE_CODE_SESSION_ID or CURSOR_SESSION_ID
  # or CURSOR_CONVERSATION_ID or "" with no trailing newline.
  python3 "$HOME/.ai-playbook/scripts/skill_gate.py" --write-marker --session-id "$SID"
  ```
  Marker filename: `plans.<project>.<session>.marker` under `~/.ai-playbook/runtime/skill-invoked/`. `project` derives inside the core via `facts_paths.resolve_project_key` (do not re-implement). `session` = `sha1(value)[:16]` hex of the session value, or literal `no-session` when empty. The CLI writes atomically at mode 0o600; a `FileExistsError`-style benign race is success; any other write failure aborts LOUDLY before the plan-file write. Acceptance window: marker mtime within 4 hours (default `SKILL_GATE_WINDOW`).

## Gist & Examples

Two workstreams in one pass.

**Workstream A (Confluence split).** `review-confluence-doc` is named as a reviewer but, since commit `20e525d`, also carries the full Confluence publication contract ("Confluence publication and diagram integrity"). That section contradicts the skill's own guideline "Do NOT modify the Confluence page content. This skill is read + comment only." This plan extracts every publish-side obligation into a new `confluence-page-sync` skill and rewire routing:

- Before: "publish my RFC to Confluence" → `review-confluence-doc` (name implies read-only; skill actually instructs full-body page replacement).
- After: "review this Confluence page" → `review-confluence-doc` (fetch, panel review, staged feedback, optional comments); "publish/sync my RFC to Confluence" → `confluence-page-sync`.
- `rfc-design` description currently says Confluence pages "use review-confluence-doc, including its publication and Mermaid diagram integrity checks"; after the split it routes reviews to `review-confluence-doc` and publication to `confluence-page-sync`.

**Workstream B (create-documentation removal).** The `create-documentation/` command layer duplicates the skill registry and violates the repo rule that skills are canonical. Disposition per file:

- `create-design-rfc.md` (11 lines): pure redirect stub to `rfc-design`; nothing to salvage; delete.
- `create-tdd.md` (1194 lines): no skill counterpart; promote to `agents/skills/tdd-design/` (SKILL.md + LICENSE.txt) with rule text preserved.
- `create-bug-ticket.md` (147 lines): already duplicated in condensed form by `jira-workflow/SKILL.md` "Bug / Incident Ticket Format" (lines 223–255); fold the two missing one-liners into that section; delete.
- Example: a user asking "create a TDD for the export service" previously loaded `create-documentation/create-tdd.md`; after removal the `tdd-design` skill triggers on "create TDD" / "technical design document" and produces the same sections 1–11 with the same completeness, traceability, and force-diff gates.

**Edge cases that motivated decisions:** Confluence retains presentation derivatives (Mermaid extension nodes) after full-body replacement, so the duplicate-detection counts (one source block, zero extension nodes, zero image embeds per diagram) must survive the move un-softened. `CLAUDE.md` is a manual near-copy of `AGENTS.md` (currently two rules behind); only removal-related edits are mirrored, the pre-existing lag is not backported.

## Evaluation Criteria

**Quality dimensions:**
- Reference integrity: final validation block green; zero stale `create-documentation` references in the tracked tree outside `docs/plans/`, `docs/tmp/`, `docs/history/`; zero publication remnants in `review-confluence-doc`; both `rfc-design` redirects present.
- Skill-design compliance (repo AGENTS.md rules): each new skill has `LICENSE.txt` (MIT, from `agents/skills/plans/LICENSE.txt`), a Configuration-from-facts section, trigger phrases, tool-agnostic wording, and no personal paths or org domains.
- Content fidelity: the five numbered publication rules from `20e525d` and the `create-tdd.md` normative rule text carry over without weakening (see Design Invariants).
- Gate fidelity: `scripts/scan-public-hygiene.sh --selftest` green after scope edit; public hygiene scan exits 0 from repo root; deployed copy at `~/.ai-playbook/scripts/` matches the repo copy.

**Done when:**
- All validation commands pass on the feature branch.
- Two scoped commits exist: Commit A (Confluence split), Commit B (tdd-design promotion + layer removal).

**Ship when:**
- None; repository-internal skill refactor with no deployed artifact.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skills, docs, scripts):**
- `agents/skills/confluence-page-sync/SKILL.md` *(new)*
- `agents/skills/confluence-page-sync/LICENSE.txt` *(new)*
- `agents/skills/tdd-design/SKILL.md` *(new)*
- `agents/skills/tdd-design/LICENSE.txt` *(new)*
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/jira-workflow/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `scripts/scan-public-hygiene.sh`
- `create-documentation/create-design-rfc.md` *(deleted)*
- `create-documentation/create-tdd.md` *(deleted)*
- `create-documentation/create-bug-ticket.md` *(deleted)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `agents/skills/tdd-guide/SKILL.md`; Kent Beck methodology skill; the `tdd-design` Core Concepts note owns the disambiguation, no edit needed here.
- `agents/skills/review-agents/**`, `agents/skills/review-staging/**`, `agents/skills/premortem/**`, `agents/skills/review-confluence-doc` review machinery, `agents/skills/rfc-design/references/eval-cases.md`; the review panel contract is untouched; `review-confluence-doc` remains a consumer unchanged. Review-round extension: fix commits r1-r5 landed sanctioned learn/generalize outputs in review machinery (review-staging snippet and digest rules, doing-code-review snippet examples, receiving-review class-exhaustive rule, plans validation rules, development_lessons 206-209) and reworded the agent-runtime-layout AGENTS.md description line; r6 fixes stayed on the must-fix paths (confluence-page-sync, doc-hierarchy), the plan's own Validation Commands block plus the Task 1 and Task 4 record notes, and development_lessons 210 (sanctioned learn output); the Workstream A/B tasks did not touch the panel contract; the fix-round learn outputs did. r7 fixes (all 7 findings) touched confluence-page-sync (Step 4 exhaustive validator-input ownership: confluence README index update, manifest entry key schema naming the top-level `pages` array, one-entry-per-page model, `sync_status` mirror refresh; plus the Documentation paths artifacts sentence), the plan's own Validation Commands block (three new probes) and this Review Scope record (r6 clause correction plus this r7 note), the r7 review staging doc and its .stats.json sidecar under docs/reviews, and the review-r7 execution log under docs/tmp (review and tmp paths are gitignored; the tracked footprint is confluence-page-sync, this plan file, and the development_lessons #210 follow-up witness paragraph). r8 fixes (all 6 findings) touched confluence-page-sync (Step 4 item 1 non-exclusive key-set wording naming the rule-5 ledger fields and the child-ID-only parent list, item 4 first-sync widening, and the Documentation paths README-index artifact clause), doc-hierarchy (integration row extended with the README page-id index), the plan's own Validation Commands block (key-schema probe repointed to the reworded span, three new probes) and this Review Scope record (r7 parenthetical correction plus this r8 note), the r8 review staging doc and its .stats.json sidecar under docs/reviews, and the review-r8 execution log under docs/tmp (review and tmp paths are gitignored; the tracked footprint is confluence-page-sync, doc-hierarchy, and this plan file, plus the development_lessons r8 witness paragraph the done learn flow will append).
- `projects/.ai-playbook/agent-runtime-layout.md`; no entry references `create-documentation`, and new first-party skills are covered by the shared-registry section exactly as `review-confluence-doc` is (no per-skill entry).
- `CLAUDE.md` backport of the two rules it lags behind `AGENTS.md`; pre-existing drift.
- `docs/history/**`; immutable archives keep old references by design.

## Design Invariants (CR Guard)

1. **Publication-rule fidelity:** the five numbered rules from commit `20e525d` move with normative strength intact: (a) full-body publish in one intentional update, never a stub probe; (b) preserve Mermaid as fenced source blocks, never add a second extension/image derivative; (c) reuse an existing extension representation only after stored-HTML inspection proves a known single-rendering pair; (d) post-publish verification through stored HTML with counts one source block, zero extension nodes, zero image embeds per diagram, plus full-body presence; (e) record `version.number`, last-modified, source revision, and sync status; `synced` only after (d) succeeds. Context rewording is allowed; dropping or softening any gate is a blocking regression.
2. **Review workflow unchanged:** `review-confluence-doc` Steps 0–6 (integration check, identify, fetch, classify, analyze, present, offer comments) stay as-is except the deleted publication section and one added redirect Integration Point. Step 6 comment posting stays.
3. **TDD rule preservation:** `create-tdd.md` normative rule text (Steps 0–4, completeness and closure, semantic non-collapse, required-fields enforcement, internal-vs-external call path, traceability, force diff completeness, sections 1–11, output contract) carries into `tdd-design/SKILL.md` without semantic change; only frontmatter, Core Concepts, heading de-emoji, Documentation paths, and Integration Points are new.
4. **Stale-reference sweep stays strict:** the `AGENTS.md` anti-duplication rule is reworded WITHOUT the literal old folder name ("do not add a parallel command-file layer that duplicates a skill in `agents/skills/`; the skill is the canonical form"), so the final zero-tolerance `git grep create-documentation` sweep has no legitimate surviving match outside excluded archive paths.
5. **Scan-script scope only:** `scripts/scan-public-hygiene.sh` keeps identical behavior for `agents/skills` and `projects`; only the three `create-documentation` scope entries (SCAN_STRICT, usage text, changed-files case) are removed, and `--selftest` stays green.
6. **Hygiene:** new skills contain no personal paths, org domains, team identifiers, or tool-specific names; each new directory carries MIT `LICENSE.txt` copied from `agents/skills/plans/LICENSE.txt`.

## Validation Commands

Final full block (run in Task 9; Task 5 runs the Workstream-A subset: checks 2, 3, 4, the `confluence-page-sync` rows of check 8, and check 10). Exclusions `:!docs/plans` `:!docs/tmp` `:!docs/history` are intentional: the plan and requirements buffer legitimately contain the swept literals (self-match immunity), and history archives are immutable.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1

# Helper: fail-closed no-match assertion (git grep exit 2 = error, not "no match").
expect_no_match() {
  git grep -qE "$1" -- "${@:2}"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "FORBIDDEN MATCH: $1 in ${*:2}"; exit 1; fi
  if [ "$rc" -ge 2 ]; then echo "GREP ERROR: $1"; exit 1; fi
}

# Helper: fail-closed rg no-match assertion (rg exit 0 = forbidden match, 1 = clean
# no-match, >= 2 = tool error such as missing ripgrep or unreadable path).
expect_rg_no_match() {
  rg -n "$1" "${@:2}"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "FORBIDDEN MATCH: $1 in ${*:2}"; exit 1; fi
  if [ "$rc" -ge 2 ]; then echo "RG ERROR (rc $rc): $1 in ${*:2}"; exit 1; fi
}

# 1. New skill directories exist with required artifacts.
for d in confluence-page-sync tdd-design; do
  test -f "agents/skills/$d/SKILL.md" || { echo "missing agents/skills/$d/SKILL.md"; exit 1; }
  test -f "agents/skills/$d/LICENSE.txt" || { echo "missing LICENSE.txt in $d"; exit 1; }
  cmp -s "agents/skills/$d/LICENSE.txt" agents/skills/plans/LICENSE.txt || { echo "LICENSE drift in $d"; exit 1; }
done

# 2. confluence-page-sync obligations (one dedicated grep per obligation; each
#    pattern is a distinctive verbatim span of the normative rule line, so no
#    probe can be satisfied by an unrelated Step/heading/reference line).
C=agents/skills/confluence-page-sync/SKILL.md
grep -q '^name: confluence-page-sync' "$C" || { echo "frontmatter name"; exit 1; }
grep -q 'Publish the complete document body in one intentional update\. Do not test connectivity by replacing a live page with a short stub' "$C" || { echo "full-body rule"; exit 1; }
grep -q 'not the editor preview and not the submitted source' "$C" || { echo "stored-HTML fetch rule"; exit 1; }
grep -q 'no duplicate extension/image derivative' "$C" || { echo "Mermaid duplicate-derivative prohibition"; exit 1; }
grep -q 'resulting Confluence `version\.number`, last-modified timestamp, source revision, and sync status' "$C" || { echo "version ledger"; exit 1; }
grep -q 'Set `synced` only after the full-body update and HTML verification succeed' "$C" || { echo "synced-after-verification gate"; exit 1; }
grep -qF 'write its mirror file `docs/history/context/confluence/{page_id}-{slug}.md`' "$C" || { echo "mirror-write rule for created pages"; exit 1; }
grep -qF 'also add the page id (with title and mirror path) to that index' "$C" || { echo "confluence README index update rule"; exit 1; }
grep -qF 'lives in the top-level `pages` array' "$C" || { echo "manifest pages-array placement rule"; exit 1; }
grep -qF 'gets its own manifest entry' "$C" || { echo "one manifest entry per page rule"; exit 1; }
grep -qF 'reads `page_id`, `slug`, `title`, `local_path`, and `layer2_targets` from each entry' "$C" || { echo "manifest entry key schema"; exit 1; }
grep -qF 'refresh the existing mirror' "$C" || { echo "mirror-refresh rule for updated pages"; exit 1; }
grep -qF '`confluence_version`, `synced_at`, and `sync_status` fields' "$C" || { echo "mirror-refresh field list"; exit 1; }
grep -q 'resolve the parent page' "$C" || { echo "parent/child creation procedure"; exit 1; }
# r9 F1: Step 2 item 4 must teach the IDs-only parent-entry shape; pin the
#        reworded span with an exact match count (grep -c exit 1 = no match,
#        exit 2 = tool error; both fail closed, and the count must equal 1).
S2N="$(grep -cF 'Record every created child page ID in the parent document' "$C")"; rc=$?
if [ "$rc" -ne 0 ] || [ "$S2N" -ne 1 ]; then
  echo "Step 2 child-record rule not pinned exactly once (rc $rc, matches ${S2N:-none})"; exit 1
fi
grep -q 'one Mermaid source block per diagram, zero Mermaid extension nodes, and zero generated image embeds' "$C" || { echo "post-publish verification"; exit 1; }
grep -q 'Default Atlassian cloud domain when the user provides no full page URL' "$C" || { echo "config-from-facts"; exit 1; }
grep -q 'existing sync manifest, conventional location `docs/maintenance/confluence-sync-manifest\.json`' "$C" || { echo "ledger anchor"; exit 1; }
grep -q 'invalid_grant' "$C" || { echo "Step 0 OAuth refresh guidance missing"; exit 1; }
grep -q 'Invalid refresh token' "$C" || { echo "Step 0 OAuth refresh guidance missing (Invalid refresh token)"; exit 1; }
grep -q 'OAuth token refresh failed' "$C" || { echo "Step 0 OAuth refresh guidance missing (OAuth token refresh failed)"; exit 1; }

# 3. review-confluence-doc: zero publication remnants, review flow intact.
R=agents/skills/review-confluence-doc/SKILL.md
if grep -niE 'publication|version\.number|sync manifest|ledger|mermaid' "$R"; then
  echo "publication remnants in review-confluence-doc"; exit 1
fi
grep -q 'Do NOT modify the Confluence page content' "$R" || { echo "read-only guideline lost"; exit 1; }
grep -q 'Offer to Post as Confluence Comment' "$R" || { echo "Step 6 comment flow lost"; exit 1; }
grep -q 'With `confluence-page-sync` skill (redirect)' "$R" || { echo "redirect Integration Point missing"; exit 1; }
# Frontmatter scope (Task 2): review+comment only. Sweep publish wording over the
# frontmatter block alone (lines between the first two --- markers); the whole-file
# sweep above stays narrow because the redirect IP legitimately says "Publishing".
FM="$(sed -n '2,/^---$/p' "$R")"
printf '%s\n' "$FM" | grep -q '^name: review-confluence-doc' \
  || { echo "frontmatter block not isolated"; exit 1; }
if printf '%s\n' "$FM" | grep -qiE 'publish'; then
  echo "publish wording in review-confluence-doc frontmatter"; exit 1
fi

# 4. rfc-design: both redirects present, old combined wording gone.
F=agents/skills/rfc-design/SKILL.md
grep -q 'With `review-confluence-doc` skill (redirect)' "$F" || { echo "review redirect lost"; exit 1; }
grep -q 'With `confluence-page-sync` skill (publication)' "$F" || { echo "publish redirect missing"; exit 1; }
grep -q 'Publish or sync an RFC/TDD to Confluence' "$F" || { echo "rfc-design Handoff row missing"; exit 1; }
grep -q 'Create a Technical Design Document (TDD)' "$F" || { echo "rfc-design TDD redirect row missing"; exit 1; }
if grep -q 'publication and Mermaid diagram integrity checks' "$F"; then
  echo "old combined redirect wording survives"; exit 1
fi

# 5. create-documentation fully removed from tracked tree (negated sweeps).
if git ls-files -- 'create-documentation' | grep -q .; then
  echo "create-documentation files still tracked"; exit 1
fi
expect_no_match 'create-documentation' ':!docs/plans' ':!docs/tmp' ':!docs/history'
expect_no_match 'create-design-rfc|create-bug-ticket|create-tdd' ':!docs/plans' ':!docs/tmp' ':!docs/history'

# 6. tdd-design content fidelity (dedicated greps per rule family) and de-emoji.
T=agents/skills/tdd-design/SKILL.md
grep -q '^name: tdd-design' "$T" || { echo "frontmatter name"; exit 1; }
grep -q 'lives in the `tdd-guide` skill' "$T" || { echo "disambiguation note missing"; exit 1; }
grep -q 'Semantic Non-Collapse' "$T" || { echo "semantic non-collapse rule lost"; exit 1; }
grep -q 'FORCE DIFF COMPLETENESS' "$T" || { echo "force-diff rule lost"; exit 1; }
grep -q 'TRACEABILITY RULES (GLOBAL)' "$T" || { echo "traceability rules lost"; exit 1; }
grep -q 'skill (publication handoff)' "$T" || { echo "confluence-page-sync handoff Integration Point missing"; exit 1; }
# Emoji headings or orphaned variation selectors must not survive in tdd-design.
expect_rg_no_match '^#{1,6} .*([\x{1F300}-\x{1FAFF}]|[\x{2600}-\x{27BF}]|\x{FE0F})' agents/skills/tdd-design/SKILL.md

# 7. jira-workflow bug-ticket deltas folded.
J=agents/skills/jira-workflow/SKILL.md
grep -qi 'abbreviation' "$J" || { echo "abbreviation rule missing"; exit 1; }
grep -q 'what to trim' "$J" || { echo "over-limit escalation missing"; exit 1; }
grep -q 'create a bug ticket' "$J" || { echo "bug-ticket trigger phrase missing"; exit 1; }
grep -q 'create an incident ticket' "$J" || { echo "incident-ticket trigger phrase missing"; exit 1; }
grep -q 'ticket type or priority' "$J" || { echo "ticket-type/priority ban missing"; exit 1; }
grep -q 'look templated or auto-generated' "$J" || { echo "anti-template output rule missing"; exit 1; }
grep -q 'Use provided textual context' "$J" || { echo "provided-context input rule missing"; exit 1; }
grep -q 'inspect relevant code to understand behavior' "$J" || { echo "code-inspection input rule missing"; exit 1; }
grep -q 'perform external research only if required' "$J" || { echo "external-research input rule missing"; exit 1; }
grep -q 'No speculation' "$J" || { echo "incident-summary speculation ban missing"; exit 1; }
grep -q 'No technical detail' "$J" || { echo "incident-summary technical-detail ban missing"; exit 1; }
grep -q 'explicitly state what is unknown' "$J" || { echo "impact-unknowns rule missing"; exit 1; }
grep -q 'If unclear, stop and ask questions' "$J" || { echo "expected-behavior stop-and-ask rule missing"; exit 1; }
grep -q 'class or method names' "$J" || { echo "acceptance-criteria class/method-name ban missing"; exit 1; }
grep -q 'navigational anchors' "$J" || { echo "identifier-anchor rule missing"; exit 1; }
grep -q 'known repro' "$J" || { echo "known-repro evidence source missing"; exit 1; }
grep -q 'no explanation of internal logic' "$J" || { echo "internal-logic explanation ban missing"; exit 1; }
grep -q 'restate the Jira summary' "$J" || { echo "supporting-doc verbatim-restatement ban missing"; exit 1; }

# 8. Catalog wiring (per-file greps: each file's obligation gated individually;
#    grep exit 2 on a missing file fires the fail branch, staying fail-closed).
#    README rows are pinned by distinctive catalog-row spans because the bare
#    skill names also appear in unrelated README usage-example and cross-reference
#    lines; the loop files each carry exactly one wiring line for the skill name.
for f in agents/skills/using-skills/SKILL.md \
         agents/skills/bootstrap-ai-playbook/SKILL.md agents/skills/doc-hierarchy/SKILL.md; do
  test -f "$f" || { echo "wiring file missing: $f"; exit 1; }
  grep -q 'confluence-page-sync' "$f" || { echo "confluence-page-sync wiring missing in $f"; exit 1; }
done
grep -q 'Technical Design Documents use' agents/skills/using-skills/SKILL.md \
  || { echo "using-skills TDD routing clause missing"; exit 1; }
grep -q 'Publishes and synchronizes local documents' README.md \
  || { echo "confluence-page-sync catalog row missing in README.md"; exit 1; }
for f in agents/skills/bootstrap-ai-playbook/SKILL.md agents/skills/doc-hierarchy/SKILL.md; do
  test -f "$f" || { echo "wiring file missing: $f"; exit 1; }
  grep -q 'tdd-design' "$f" || { echo "tdd-design wiring missing in $f"; exit 1; }
done
grep -q 'Generates a Technical Design Document with strict completeness rules' README.md \
  || { echo "tdd-design catalog row missing in README.md"; exit 1; }
grep -q 'Bug / Incident Ticket Format' README.md || { echo "bug-ticket README row missing"; exit 1; }
grep -qF 'publishing via `confluence-page-sync`' README.md \
  || { echo "README rfc-design publish clause missing"; exit 1; }

# 9. Scan script: scope entries removed, selftest green, deployed copy synced.
if grep -n 'create-documentation' scripts/scan-public-hygiene.sh; then
  echo "scan script still scans removed folder"; exit 1
fi
bash scripts/scan-public-hygiene.sh --selftest || { echo "selftest failed"; exit 1; }
cmp -s scripts/scan-public-hygiene.sh "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" \
  || { echo "deployed scan script differs from repo copy"; exit 1; }

# 10. Hygiene: no absolute personal paths in new skills; public scan exit 0.
expect_rg_no_match '/Users/' agents/skills/confluence-page-sync agents/skills/tdd-design
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) \
  || { echo "public hygiene scan failed"; exit 1; }
echo "ALL VALIDATIONS PASSED"
```

Simulation note (rule 10): removing any single obligation above (delete a dedicated grep's target rule, keep a `create-documentation` reference, skip the redeploy) makes the corresponding check exit non-zero; the negated sweeps invert correctly because matches are failures and grep errors (exit 2) abort separately; the rg-based sweeps use `expect_rg_no_match` with the same rc-splitting (rc 0 = forbidden match fails, rc 1 = clean pass, rc >= 2 = tool error such as missing ripgrep fails).

### Task 1: Create the confluence-page-sync skill

Files:
- `agents/skills/confluence-page-sync/SKILL.md` *(new)*
- `agents/skills/confluence-page-sync/LICENSE.txt` *(new)*

- [x] Frontmatter: `name: confluence-page-sync`; description states ownership of Confluence publishing/synchronization with trigger phrases ("publish to Confluence", "sync RFC to Confluence", "update Confluence page", "create child page"); explicitly not a review skill.
- [x] Core Concepts: repository document as source of truth vs page as rendered derivative; sync manifest/ledger; single-rendering pair.
- [x] `## Configuration (from facts document)` section: `atlassian_domain` key, purpose, fallback guidance per the repo skill-design rules (no hardcoded domains).
- [x] Step 0 prerequisite: verify Atlassian integration with BOTH page fetch and page update capability; reuse the `review-confluence-doc` Step 0 unavailable-message and OAuth refresh-error guidance (`invalid_grant`, `Invalid refresh token`, `OAuth token refresh failed`); STOP for the user when unavailable.
- [x] Publication rules: move the five numbered rules of `review-confluence-doc` §"Confluence publication and diagram integrity" (lines 34–44 at commit `20e525d`) with normative text intact (Design Invariant 1), including the closing paragraph on presentation derivatives surviving full-body replacement.
- [x] Parent/child page creation: resolve the parent page ID (URL, title+space key, or page ID inputs, mirroring `review-confluence-doc` Step 1 acceptance); create child pages for document parts (appendices, sub-documents); record created child page IDs and titles in the ledger entry.
- [x] Post-publish verification procedure: fetch stored HTML (not editor preview); count Mermaid source blocks, extension nodes, image embeds; expected one source block per diagram, zero extension nodes, zero generated image embeds for native fenced-block targets; confirm full body present.
- [x] Ledger rules: record `version.number`, last-modified timestamp, source revision, sync status in the repository's existing sync manifest (`docs/maintenance/confluence-sync-manifest.json` convention; `scripts/confluence-mirror-hygiene.sh validate` checks it); set `synced` only after full-body update and HTML verification both succeed.
- [x] Integration Points (bidirectional per repo rules): `rfc-design` (publication handoff consumer), `review-confluence-doc` (redirect provider), `doc-hierarchy` (manifest and mirror placement under `docs/history/context/confluence`).
- [x] Copy `agents/skills/plans/LICENSE.txt` to `agents/skills/confluence-page-sync/LICENSE.txt`.
- [x] Tool-agnostic wording pass: no tool names, no agent type names; behaviors described by intent ("ask the user", "fetch the page").

Review-round extension: plus a done/docs-branch session-end sync hygiene entry added in review rounds; r6 added the Step 4 mirror-write sub-item (created pages get a `docs/history/context/confluence/{page_id}-{slug}.md` mirror with the standard frontmatter and `local_path` recorded; updated pages refresh `confluence_version` and `synced_at`).

### Task 2: Slim review-confluence-doc to review-only

Files:
- `agents/skills/review-confluence-doc/SKILL.md`

- [x] Delete the section `### Confluence publication and diagram integrity` (between `## Workflow` and `### Step 0`); nothing else in Steps 0–6 changes.
- [x] Keep the Guidelines line "Do NOT modify the Confluence page content. This skill is read + comment only." (contradiction from `20e525d` now resolved).
- [x] Add Integration Point `### With confluence-page-sync skill (redirect)`: publishing, page updates, and diagram-integrity checks are owned by `confluence-page-sync`; redirect such requests there (wording must avoid the swept tokens: no "publication", "Mermaid", "ledger", "version.number", "sync manifest").
- [x] Frontmatter description stays review+comment scoped (no publish wording present today; verify none was added).

### Task 3: Rewire rfc-design routing

Files:
- `agents/skills/rfc-design/SKILL.md`

- [x] Frontmatter description: replace "Confluence-hosted pages: use review-confluence-doc, including its publication and Mermaid diagram integrity checks." with two clauses: hosted-page reviews use `review-confluence-doc`; publishing/synchronizing to Confluence uses `confluence-page-sync`.
- [x] `## When to Use` table: update the Redirect row (review only); add row `| Publish or sync an RFC/TDD to Confluence | **Handoff** | confluence-page-sync (page updates, Mermaid integrity, ledger) |`.
- [x] "Do not use" line: append `or Confluence publishing (confluence-page-sync)`.
- [x] Integration Points: rewrite `### With review-confluence-doc skill (redirect)` to review-only; add `### With confluence-page-sync skill (publication)` describing the handoff (this skill owns local Markdown authoring; the page is a rendered derivative).

Extended in review rounds r1-r2: r1 added the tdd-design routing clauses (frontmatter description clause, When-to-Use TDD redirect row, do-not-use line); r2 retitled the stale `# Command:` header to `# rfc-design:`.

### Task 4: Workstream-A catalog wiring

Files:
- `README.md`
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`

- [x] `README.md` command catalog: add `confluence-page-sync` row (path `agents/skills/confluence-page-sync/SKILL.md`; publishes/synchronizes local documents to Confluence with Mermaid integrity and version ledger); update the `rfc-design` row's Confluence clause to "reviews via `review-confluence-doc`; publishing via `confluence-page-sync`".
- [x] `agents/skills/using-skills/SKILL.md` item 9: extend with publishing clause ("publishing/syncing a document to Confluence uses `confluence-page-sync`").
- [x] `agents/skills/bootstrap-ai-playbook/SKILL.md` consumer table (row listing `review-confluence-doc`, `rfc-design`): add `confluence-page-sync` with note it reads `{tmp_dir}` for fetch/HTML scratch from the facts TOML.
- [x] `agents/skills/doc-hierarchy/SKILL.md` Integration table: add `confluence-page-sync` row (reads `{tmp_dir}` scratch; writes sync manifest under `docs/maintenance/` and mirrors under `docs/history/context/confluence` per `confluence-mirror-hygiene.sh`).

Extended in review round r1: using-skills item 9 also routes Technical Design Documents to `tdd-design`; the bootstrap consumer row was split so `confluence-page-sync` stands alone with its `{tmp_dir}` scratch note. r6 tightened the doc-hierarchy row to "writes or refreshes page mirrors for the pages it publishes (Step 4)", matching the Step 4 mirror-write sub-item.

### Task 5: Workstream-A validation subset and Commit A

Files:
- (no file edits; validation and commit)

- [x] Run validation checks 2, 3, 4, the `confluence-page-sync` rows of check 8, and check 10 from the Validation Commands block; all green. For check 10's `/Users/` sweep at this interim point, scope the rg to `agents/skills/confluence-page-sync` only (`agents/skills/tdd-design` does not exist until Task 6; an rg over a missing path exits 2 and the if-then fail branch never fires, making the interim sweep vacuously green); the full two-directory sweep runs in Task 9.
- [x] Commit A on the feature branch: `skills: extract confluence-page-sync from review-confluence-doc` (tasks 1–4 files only; `create-documentation/` untouched so the tree stays consistent).

### Task 6: Promote create-tdd.md to the tdd-design skill

Files:
- `agents/skills/tdd-design/SKILL.md` *(new)*
- `agents/skills/tdd-design/LICENSE.txt` *(new)*
- `create-documentation/create-tdd.md` (source; deleted in Task 7)

- [x] Frontmatter: `name: tdd-design`; description "Create Technical Design Documents (TDD) in Markdown with exhaustive, implementation-grade completeness rules" with trigger phrases ("create TDD", "technical design document", "TDD for <feature>").
- [x] Core Concepts: TDD here means Technical Design Document; test-driven development methodology lives in `tdd-guide`; summarize the rule families (completeness and closure, semantic non-collapse, required-fields enforcement, internal-vs-external call path, traceability, force diff completeness).
- [x] Copy all normative sections from `create-documentation/create-tdd.md` preserving rule text (Design Invariant 3): Steps 0–4, global rules, section-by-section requirements 1–11, output formatting rules, final output contract.
- [x] Normalize emoji in SECTION HEADINGS to plain text (for example `### 1. 🧭 Introduction` → `### 1. Introduction`; strip the trailing variation selector U+FE0F that rides some heading emoji, so no invisible orphan remains). Emoji inside preserved body rule-text lines (for example the `🎯` on `create-tdd.md` line 102) remain untouched: rule text carries over intact per Design Invariant 3.
- [x] Add `## Documentation paths` section: resolve `{rfcs_dir}` / `{proposals_dir}` from the facts TOML per `using-skills` Step 0; finished TDDs are Layer 3 history files like RFCs; drafts under `{proposals_dir}` when present.
- [x] Integration Points: `review-confluence-doc` (published TDD review consumer), `rfc-design` (sibling RFC generator), `tdd-guide` (disambiguation), `bootstrap-ai-playbook` (path-key consumer).
- [x] Copy `agents/skills/plans/LICENSE.txt` to `agents/skills/tdd-design/LICENSE.txt`.
- [x] Tool-agnostic wording pass (same bar as Task 1).

Extended in review round r1: added the `confluence-page-sync` publication-handoff Integration Point, extended the `review-confluence-doc` entry with the technical-vs-test-design disambiguation, and fixed the Output Formatting heading to Do NOT Simplify Skill.

### Task 7: Fold bug-ticket deltas into jira-workflow; delete create-documentation

Files:
- `agents/skills/jira-workflow/SKILL.md`
- `create-documentation/create-design-rfc.md` *(deleted)*
- `create-documentation/create-tdd.md` *(deleted)*
- `create-documentation/create-bug-ticket.md` *(deleted)*

- [x] In `jira-workflow` §"Bug / Incident Ticket Format": add abbreviation rule from `create-bug-ticket.md` ("Abbreviations may be used, but MUST be clarified in parentheses on first use, e.g. MQ (message queue)") and over-limit escalation ("if still over 800 characters after rewrite, stop and ask the user what to trim"); no other changes to the section.
- [x] `jira-workflow` frontmatter description: add trigger phrases "create a bug ticket", "create an incident ticket".
- [x] After Task 6 content checks pass, `git rm create-documentation/create-design-rfc.md create-documentation/create-tdd.md create-documentation/create-bug-ticket.md`.

Extended in review rounds r1-r4: additional create-bug-ticket clauses restored per UL#207.

### Task 8: Reference removal and scan-script scope

Files:
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `scripts/scan-public-hygiene.sh`

- [x] `AGENTS.md`: remove the `create-documentation/` structure bullet; replace the registration `cp` block with a note that commands live as skills under `agents/skills/` (register/alias per-agent as needed); update the direct-mode `codex exec` example to cat a skill file (`agents/skills/tdd-design/SKILL.md`); update the filename-convention example away from `create-design-rfc.md`; reword the anti-duplication rule without the literal folder name (Design Invariant 4); update the commit-style example to `skills: <concise summary>`.
- [x] `AGENTS.md` + `CLAUDE.md` identity lines (survive token sweeps, update explicitly): line 4 "This repository is a command-spec library" → skill-library wording; line 8 "source-of-truth index for command catalog, usage, and registration examples" → index for the skill catalog and usage.
- [x] `CLAUDE.md`: mirror exactly the same removal-related edits (do not backport unrelated rules it lags).
- [x] `README.md`: remove the `create-documentation/` subtree from the directory tree and the folder bullet; replace catalog rows: `create-bug-ticket` → `jira-workflow` skill path (Bug / Incident Ticket Format section), `create-design-rfc` → `rfc-design` skill only (drop redirect-stub mention), `create-tdd` → `agents/skills/tdd-design/SKILL.md`; remove the `.opencode/command` registration snippet and slash-command examples; update direct-mode `cat` examples to the skill files.
- [x] `README.md` usage-model prose (survives token sweeps, update explicitly): rewrite the "What This Repo Is" sentence and the two usage-mode bullets (lines 4, 8–10) so the repo is described as a skill library under `agents/skills/` loaded per agent, not a copy-into-`.opencode/command` command registry; replace the "Usage Examples (Hybrid)" registered-command section (lines 102–116) with skill invocation plus direct-mode `cat` of a `SKILL.md`; rename "How to Add a New Command" (lines 147–152) to "How to Add a New Skill" with steps (create `agents/skills/<name>/SKILL.md` + `LICENSE.txt`, update the README catalog, add bidirectional Integration Points, run the hygiene scan); update the "Current Status" line (176) that says all files are used as command files.
- [x] `bootstrap-ai-playbook` consumer table: add `tdd-design` (reads `{rfcs_dir}`/`{proposals_dir}`); `doc-hierarchy` Integration table: add `tdd-design` row (Layer 3 history placement like `rfc-design`).
- [x] `scripts/scan-public-hygiene.sh`: remove `create-documentation` from `SCAN_STRICT`, from the usage text, and from the changed-files `case` pattern; run `--selftest` (green required).
- [x] Redeploy: back up `~/.ai-playbook/scripts/scan-public-hygiene.sh` to `scan-public-hygiene.sh.bak-$(date +%Y%m%d)`, then copy the repo script over it.

Extended in review rounds r1 and r3: r1 reworded the README title, Skill Catalog heading, and learn bullet to skill-era wording; r3 reworded the remaining command-era bullets in `AGENTS.md` and `CLAUDE.md` to skill vocabulary and added the Integration Points verify-against-peer clause to the skill-design guidelines (both mirrored files).

### Task 9: Full validation and Commit B

Files:
- (no file edits; validation and commit)

- [x] Run the complete Validation Commands block; terminate with `ALL VALIDATIONS PASSED`.
- [x] Commit B on the feature branch: `skills: promote create-tdd to tdd-design; remove create-documentation layer` (tasks 6–8 files).
- [x] Report both commits and remaining follow-ups (branch push stays off until the user asks).
