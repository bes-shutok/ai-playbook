# Plan: Done sensitive-data scan visibility-scoped redaction

Backlog origin: docs/history/backlog/2026-09-28-secret-scan-preserve-valid-service-links.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-done-scan-visibility-scoped-redaction-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The done workflow's sensitive-data scan stops erasing valid internal service links in repositories that declare themselves private, while keeping credential detection active in every repository and the public-artifact strictness everywhere else.

- A consumer closeout in a private company repository can keep its ordinary internal Jira links (no credential, token, or secret query value) without a host-only redaction that changes the plan digest and stales the review record.
- Repositories that declare no visibility keep today's strict behavior, so no existing consumer scan silently weakens.
- The remediation guidance distinguishes public-artifact redaction from credential resolution, so the fix for a flagged link matches why it was flagged.

Gate delta: no refusal class is added; the change removes false-positive refusals for private-declared repositories by splitting one pattern constant into two named families and gating one family on a new repo-facts key read (`artifact_visibility`), which is the fix-class sanctioned exit the origin prescribes (the class-defaults are why this is an exit and not an addition: the false positive is the hostname/contact pattern family applied outside its public-artifact audience, and removing the block for private repos while keeping credential refusals is exactly the origin's first Expected bullet).

## Terms

- **Credential-shaped pattern**: a deny pattern that matches secret material forms (API key, token, password or secret assignment); active in every repository regardless of visibility.
- **Public-artifact pattern family**: the deny patterns whose purpose is public-artifact hygiene (local filesystem paths, employer Atlassian hostname, generic contact emails); applied only when the repository does not declare private visibility.
- **`artifact_visibility`**: the repo-scoped facts key (`.ai-playbook/facts.md`, TOML) declaring the repository's audience; value `private` or `public`; absent or unparseable reads as `public` (fail-safe: today's strictness).
- **Visibility-scoped arm**: a sensitive-data-scan content arm (staged diff content, untracked content) whose pattern set depends on `artifact_visibility`.

## Assumptions

- assume the fail-safe default when `artifact_visibility` is absent or malformed is `public` (today's strict behavior); basis: the origin's Expected bullet "public-artifact hygiene may need to redact employer-specific hostnames, but that rule should not erase valid links in private company repositories" requires an explicit private declaration, and an undeclared repository must not silently weaken its scan.
- assume visibility is a repository property and therefore a repo-scoped facts key read via the existing `facts_paths` helpers, not a user-facts table row; basis: `GateContext` already resolves every repo-scoped path through `facts_paths` against the repo root (`_resolve_dir`), and the origin says "repository visibility or an explicit confidentiality policy", which is per-repo state.
- assume the witnessed defect lives in the staged-diff and untracked content arms only (the pre-commit scan); the push-range commit-message audit (arm 3, user-facts-resolved employer-brand patterns over the push range) and the skills-repo public-hygiene arm (arm 4, this repo IS the public skills repo) are out of scope; basis: the origin's Exact location names the "pre-commit sensitive-data-scan gate and its remediation guidance", and its Problem paragraphs witness staged/untracked content flagging only.
- assume the origin item's classification is fix-class; basis: the item declares `Class: correctness` and the body records a witnessed host-only redaction false positive in a private consumer repository with a scoped-narrowing remedy; the re-derived fix-class (a false-positive removal) agrees with the declared class, so the arms shape as the fix-class sanctioned exit under the filing-class rule.
- assume the repository's pytest-runner contract applies to the new tests (venv interpreter first, ambient fallback with a version guard); basis: plan `docs/history/plans/completed/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation) records this exact contract for this same test file (the citation path is the completed/ archive location verified on this tree).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the done sensitive-data scan splits its deny patterns into credential-shaped (always active) and public-artifact families (active unless the repo declares private), so a private company repository keeps its internal Jira links; the driving force is code-quality (the scan's refusal must match its reason).

Before (today): a closeout in a company repository stages a plan line carrying `https://company.atlassian.net/browse/TEAM-123` (no credential). The pre-commit sensitive-data-scan gate fails the commit on pattern `\.atlassian\.net`; the operator strips the hostname, the plan digest changes, the review record goes stale, and a fresh review round is burned. Authoring probe on this tree confirmed the behavior: an untracked `brag.md` with a bare internal Jira link fails the gate today with `content matches pattern /\.atlassian\.net/`.

After (this plan): the consumer repo declares `artifact_visibility = "private"` in its `.ai-playbook/facts.md`. The same link passes the gate unchanged; a credential-bearing file (`api_key = "AKIA..."`) still fails it. A repository without the declaration fails the same link exactly as today. The remediation guidance sends hostname hits in private repos nowhere (they do not fire) and credential hits to the credential resolution path in every repository.

Pattern-family split being pinned:

- `CREDENTIAL_CONTENT_PATTERNS` (always active, every repository): the three assignment-shape patterns already in `DIFF_CONTENT_PATTERNS` (API key, token, password/secret).
- `PUBLIC_ARTIFACT_CONTENT_PATTERNS` (active unless `artifact_visibility = "private"`): the four audience patterns (the two home-directory path prefixes, the internal tracker host suffix, generic contact email).

## Evaluation Criteria

**Quality dimensions:**
- correctness: a private-declared repository passes valid internal service links through the staged and untracked arms while credential-shaped material still fails in the same repository; an undeclared or public repository fails the same link exactly as today.
- regression safety: every pattern in today's `DIFF_CONTENT_PATTERNS` survives in exactly one of the two new families (nothing silently dropped); the arms' findings message records which families ran.
- maintainability: the split is pinned by tests naming both constants; the skill guidance names the facts key and its default so a consumer can declare visibility without reading the lib.

**Done when:**
- `scripts/done_sweep_gates_lib.py` carries the two-family split, the `artifact_visibility` read, and the visibility-scoped arms.
- `scripts/test_done_sweep_gates_lib.py` carries the private-pass/credential-fail tests, the undeclared-repo regression test, and the family-coverage pin.
- `agents/skills/done/SKILL.md` gate description and remediation guidance carry the visibility scoping and the facts-key documentation.
- All Validation Commands exit 0 from the worktree root.

**Ship when:**
- The deployed runtime-home twin of the lib (`~/.ai-playbook/scripts/done_sweep_gates_lib.py`, a real copy, not a symlink) is refreshed from the repo copy at execution closeout, and consumer repositories declare `artifact_visibility` in their own facts documents when they want the private behavior; no further release action belongs to this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Documentation:**
- `agents/skills/done/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/scan-public-hygiene.sh` and its patterns file; reason: arm 4 is the skills-repo-only hygiene scan, which is genuinely public-audience and untouched by the witnessed defect.
- The push-range commit-message audit's pattern resolution; reason: a different arm with different (user-facts) inputs, unwitnessed by the origin.

## Validation Commands

```bash
# Runner contract: venv pytest interpreter first, ambient fallback with a loud guard.
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The new visibility-scoped tests pass.
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k visibility_scoped -q || { echo "FAIL: visibility-scoped tests" >&2; exit 1; }

# 2. The whole lib suite still passes (regression net).
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo "FAIL: lib suite" >&2; exit 1; }

# 3. Family-coverage pin: the old constant is fully partitioned (every old pattern survives in exactly one family) and the families are disjoint.
python3 - <<'PYEOF' || { echo "FAIL: family coverage" >&2; exit 1; }
import sys
sys.path.insert(0, "scripts")
import done_sweep_gates_lib as lib
old = [r"/Use" "rs/", r"/ho" "me/", r"\.atlass" "ian\.net", r"@[a-z]" r"+\.(com|io|net)", r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}", r"(?i)\b(?:access|auth|claim|policy|refresh|session)?[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}", r"(?i)\b(?:password|secret)\s*[:=]\s*\S+"]
cred, pub = set(lib.CREDENTIAL_CONTENT_PATTERNS), set(lib.PUBLIC_ARTIFACT_CONTENT_PATTERNS)
assert not (cred & pub), "families overlap"
assert cred | pub == set(old), "old set not fully partitioned"
print("family coverage ok")
PYEOF

# 4. The skill guidance carries the visibility scoping, the facts key, and the default (dedicated pins).
grep -qF 'artifact_visibility' agents/skills/done/SKILL.md || { echo "FAIL: facts key missing from skill" >&2; exit 1; }
grep -qF 'active unless the repository declares `artifact_visibility = "private"`' agents/skills/done/SKILL.md || { echo "FAIL: scoping sentence missing" >&2; exit 1; }
grep -qF 'absent or unparseable reads as `public`' agents/skills/done/SKILL.md || { echo "FAIL: default sentence missing" >&2; exit 1; }

# 5. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the behavioral probe ran against today's lib before this plan was written and recorded the witnessed defect live (untracked valid Jira link fails with `content matches pattern /\.atlassian\.net/`, credential control fails as required); the pre-round structural gate, the em-dash `touched` scan, and the public-hygiene scan ran over these plan bytes before round 1. RED-today evidence, rule 19: Validation Command 3 cannot pass against today's lib (the family constants do not exist yet), and the private-pass test prescribed by Task 1 fails against today's gate per the probe; Command 4's skill pins fail against the unamended SKILL.md (all three spans verified absent today). Rule 22 mechanical audit: each Validation Command pin occurs exactly once in its owning Task's prescribed snippet beside its Command occurrence (the rule-36 mirror carve-out; plan-wide mentions in Terms are not pin sites), and `bash -n` over this block passed.

### Task 1: Pin the visibility-scoped contract (RED)

Files:
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k visibility_scoped -q`; covers: the private-pass and default-strictness tests exist and fail against the unsplit lib.

- [ ] Add tests named with the `visibility_scoped` marker substring leading each name (pytest `-k visibility_scoped` matches name substrings, so every selected test must carry the substring), patterned on the existing `sweep_env` + `mktemp_repo` + `ctx_for` fixtures, each building a scratch repo with a committed file and an untracked file carrying `https://company.atlassian.net/browse/TEAM-123` (no credential) plus a separate credential-bearing control file; the repo facts file (`.ai-playbook/facts.md`) carries the visibility declaration inside its TOML fence (the only block `facts_paths.resolve_toml_key_raw` parses), written in the same fenced form the existing `write_facts` helper uses: `test_visibility_scoped_private_repo_passes_valid_service_link` (declaring `artifact_visibility = "private"`; the test then stages the Jira-link file with `git add` so the staged-diff arm carries its own pass witness alongside the untracked arm, and the gate returns rc 0 with the credential control file absent, and rc 1 when only the credential control is added); `test_visibility_scoped_undeclared_repo_keeps_strict_default` (no facts key; the Jira-link file fails rc 1 exactly as today, naming the `\.atlassian\.net` pattern); `test_visibility_scoped_public_declaration_keeps_strict_default` (explicit `artifact_visibility = "public"`; same failure); `test_visibility_scoped_private_repo_still_fails_credentials` (private declaration; the credential control alone fails rc 1). [class: REPOSITORY_TEST]
- [ ] Add `test_visibility_scoped_families_partition_the_old_constant`: both constants exist, are disjoint, and their union equals the seven patterns of today's `DIFF_CONTENT_PATTERNS` (the same assertion Validation Command 3 makes; carrying the marker substring keeps it under the Command 1 selector too). [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k visibility_scoped -q` exits non-zero (the constants and the visibility read do not exist yet; the strictness tests fail because the split does not exist, the private-pass test fails per the authoring probe). [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin visibility-scoped sensitive-data scan contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Split the pattern families and gate them on declared visibility (GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers: the new tests pass and the whole lib suite stays green.

- [ ] Split `DIFF_CONTENT_PATTERNS` into `CREDENTIAL_CONTENT_PATTERNS` (the three assignment-shape patterns, byte-identical) and `PUBLIC_ARTIFACT_CONTENT_PATTERNS` (the four audience patterns, byte-identical) and remove the old name: the authoring-time reference check found both usage sites inside `gate_sensitive_data_scan` itself and none elsewhere in the module or the `done_sweep_gates.sh` wrapper, so no alias survives. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a `GateContext` helper `artifact_visibility()` reading the repo facts TOML key `artifact_visibility` through `facts_paths.resolve_toml_key_raw` against `repo_root`, returning `private` only on an exact case-insensitive match, anything else (absent, malformed, other values) reading as `public`. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `gate_sensitive_data_scan`, make arms 1 and 2 iterate `CREDENTIAL_CONTENT_PATTERNS` always and `PUBLIC_ARTIFACT_CONTENT_PATTERNS` only when `artifact_visibility() != "private"`, and record in the gate's success message which families ran (for example `content families: credential+public-artifact` or `content families: credential (repo declares private visibility)`); arms 3 and 4 unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: scope done sensitive-data scan audience patterns by declared repo visibility` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Skill guidance and facts-key documentation (GREEN)

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- Validation Command 4's three pins pass against the amended SKILL.md.

- [ ] Amend the sensitive-data-scan gate description (the Gates-run-in-this-order bullet) to state the visibility scoping: the staged-diff and untracked content arms always run the credential-shaped patterns and run the public-artifact pattern family (local paths, employer hostname, generic contact emails) active unless the repository declares `artifact_visibility = "private"` in its `.ai-playbook/facts.md`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend the sensitive-data-scan remediation guidance bullet to scope the hostname/contact redaction sentence to public-audience artifacts and to state that a private-declared repository keeps valid internal service links, with the default sentence: the key is absent or unparseable reads as `public` (today's strictness), and credential material is resolved in every repository. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Command 4's three pins pass; `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: scope done scan remediation guidance by declared repo visibility` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Whole-plan validation gate

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

Evidence:
- The full `## Validation Commands` block run from the worktree root; covers: every criterion in Done when.

- [ ] Run the complete `## Validation Commands` block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for visibility-scoped redaction` [class: REPOSITORY_TEST]

The Ship-when deployment step (deployed twin refresh) is host-write work outside the repository and is executed at closeout, never as a plan checklist item.
