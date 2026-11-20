# Plan: release publish-scope hygiene check

Backlog origins (scope of record):
- docs/history/backlog/2026-11-08-release-publishes-tracked-ignored-files.md
- docs/history/backlog/2026-11-08-release-publishes-charter-empty-dir-rows.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-release-publish-scope-hygiene-check-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.5h total, largest task 1h
Executed: yes (48930e2d0)
Authoring claim: release-publish-scope-hygiene-check.md (session sess_5fd706c9-4024-41e8-8071-8cbef294ceda)

## Terms

- publish delta: the commit range `<remote>/main..main` and the files it changes; everything a release sends to the remote for the first time.
- delta file list: the paths changed across the publish delta, one per line, as `git diff --name-only` reports them.
- publish-scope check: the new warning-only check this plan adds: it asks whether each delta file may be tracked at all and whether it sits in a directory a repo charter requires to stay empty.
- `PUBLISH SCOPE` banner: the stderr output header the rewrite step prints ahead of any checker report lines it relays.
- `RELEASE_PUBLISH_SCOPE_CHECKER`: the Configuration-table key naming the repo-relative checker path the rewrite step invokes.
- tracked-but-ignored file: an index-tracked path that an ignore rule matches, enumerated by `git ls-files -i -c --exclude-standard`.
- charter-empty directory: a directory whose governing charter requires it to stay empty of dated item files; this repository's list lives repo-side, seeded with `docs/history/backlog/completed`.
- warning-only: the check reports and never aborts; promotion to blocking is a later, separately gated change.
- privacy scanner: the existing release content gate (`RELEASE_HYGIENE_SCANNER`, default `scripts/scan-public-hygiene.sh`) that reads blob bytes for deny patterns; its scope is frozen by this plan.
- registry-removal row: a pre-registered row in `scripts/machinery_registry.json` naming what a machinery removal will delete, its promotion criteria, and its sunset.
- the swap: the compare-and-swap that moves `main` to the rewritten tip in `release-rewrite.sh`.

## Why

The 2026-11-08 release published files no release step ever checks for: two execution-completion records force-added from the wholesale-ignored audit home, and four backlog rows parked under a directory whose charter requires it to stay empty. Repair took an operator-directed history rewrite and a force-push. The release flow's only content gate reads blob bytes, so tracking-state and charter violations reach the remote silently.

## Gist & Examples

TLDR: the release gains one configuration-keyed publish-scope checker over the delta file list, reporting tracked-but-ignored and charter-empty-directory files before the swap, because blob-pattern scanning alone let both leak classes publish.

Concretely, the witnessed 2026-11-08 release carried `.ai-playbook/reviews/*-exec-r1.md` records that were gitignored-but-tracked, and four dated rows under `docs/history/backlog/completed/` that the directory's own README forbids. After this plan, a release whose pile carries either class prints a `PUBLISH SCOPE` banner naming each offending path and its class, and the release still succeeds; the operator sees the leak before it is published instead of repairing remote history afterward. The check runs inside `release-rewrite.sh` before the swap, in the ordinary and recovery paths, and is configured by a `RELEASE_PUBLISH_SCOPE_CHECKER` key shaped like the existing `RELEASE_HYGIENE_SCANNER` key, so the skill text stays free of repo-specific paths and the deny-class knowledge lives in the repository's own checker script.

## Outcome

A release can no longer silently publish files that should never have been tracked: the delta is screened for tracking-state and charter violations before the swap, the report lands in the run output, and the convention text stops inviting the drift.

- Tracked-but-ignored files in the publish delta are named in the release run output before publication.
- Files under a repo-declared charter-empty directory are named the same way.
- The machinery is registered warning-only with its removal pre-registered, per the machinery admission protocol.
- New records stop citing completed-home backlog twins as their durable home, closing the drift invitation the old clause carried.

Gate delta: +1 warning-only check (one repo-side checker script and one release-step invocation) with its machinery-registry entries row and pre-registered removals row; +1 AGENTS.md citation-clause amendment, one doc-registry header sentence, and one lessons-corpus precedence parenthetical (lesson #4948); removes nothing; priced by the completed integrity failure both origin rows witness (the 2026-11-08 publication and the operator-directed force-push repair); gate liveness ledger at authoring time: sensitive-data-scan catches=1 incidents=3, archive-ceremony catches=1 incidents=2.

## Assumptions

- assume the checker is invoked over stdin, one path per line; basis: argv limits on large deltas; the wiring adds the `git diff --name-only` enumeration over the already-fetched range (the release scripts enumerate delta commits and the tip tree, not the file list).
- assume the charter-empty list is the checker's repo-side default constant citing the charter README as the rule's home, with no env override; basis: the facts document is gitignored and per-checkout, so a facts key alone fails on fresh clones; the charter README has no mechanical list surface; an override key would be configuration nothing sets and the release skill never documents; the origin row's constraint is that the list is never hardcoded in the skill, which a repo-side script honors.
- assume a checker nonzero exit is a tool failure and the release step prints one warning line and continues; basis: the warning-only posture and the origin rows' false-positive cost arms.
- assume a configured-but-missing checker path prints one skip line and continues; basis: warning-only machinery must not break releases on repos that have not deployed the script; the em-dash checker's missing-script abort is a blocking gate's rule, deliberately not copied.
- assume the check runs in both the ordinary and recovery rewrite paths over the same publish-delta range; basis: the recovery mode publishes a rebuilt delta crossing the same publication boundary.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the checker's deny classes are verified against real temporary-repository fixtures in pytest, not by inspection alone.
- compatibility: the release exit codes (0/1/2/3), the privacy gate contract, and the existing `test_release_skill_selftest.py` behavior stay unchanged.
- admission: the machinery-registry rows load, match existing row shapes, and carry the incident, expected catch, false-positive cost, and review date fields.
- convention: the AGENTS.md clause names the covering plan's completed twin as the citation home and names a completed-home backlog twin legacy-only.

**Done when:**
- `pytest scripts/test_release_publish_scope_check.py scripts/test_release_skill_selftest.py` passes.
- `bash scripts/release_publish_scope_check.sh --selftest` exits 0.
- A release-run output containing a tracked-ignored delta file shows the `PUBLISH SCOPE` banner followed by a `PUBLISH-SCOPE:` report line naming it, with the run's exit code and the rewrite step's single-line stdout contract unchanged.
- `python3 -c "import json;json.load(open('scripts/machinery_registry.json'))"` succeeds and the new rows carry the admission fields.

**Ship when:**
- Promotion of the check to blocking happens only after a true catch is recorded in `scripts/gate_liveness_ledger.json` and the pre-registered removals row is executed with an explicit exemption mechanism; review date 2026-12-08.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/release_publish_scope_check.sh` (Task 1) *(new)*
- `scripts/release-rewrite.sh` (Task 2)
- `scripts/machinery_registry.json` (Task 3)
- `agents/skills/release/SKILL.md` (Task 2)
- `AGENTS.md` (Task 4)
- `docs/maintenance/document-registry.md` (Task 4)
- `docs/maintenance/development_lessons.md` (Task 4; lesson #4948 parenthetical only, the file is otherwise frozen per the out-of-scope list)

**Tests:**
- `scripts/test_release_publish_scope_check.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/scan-public-hygiene.sh`; reason: the scanner's blob-pattern scope stays frozen; the delta-tracking and charter classes are a separate checker family per the dispatch entry's rejected-alternative record (family mixing) and the origin rows' single-extension-point direction.
- `scripts/check_plan_origins_closed.py`, `docs/history/backlog/completed/**`, `agents/skills/doc-hierarchy/**`; reason: the origins-gate flip and the legacy-row sweep are the sibling row's owned arm (docs/history/backlog/2026-11-08-backlog-completed-dir-regrowth.md), coordinated not absorbed.
- `docs/maintenance/development_lessons.md` lessons #104, #111, and #207 rule wording; reason: that re-wording is the sibling row's licensing-text arm, not this plan's Task 4 scope (which owns only the #4948 parenthetical).
- `scripts/release-authoring.sh`; reason: no authoring-step change; the check reads the delta before the swap in the rewrite step only.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_release_publish_scope_check.py scripts/test_release_skill_selftest.py -q
bash scripts/release_publish_scope_check.sh --selftest
python3 -c "import json;json.load(open('scripts/machinery_registry.json'))"
python3 scripts/machinery_inventory.py --check
python3 scripts/doc_registry_validator.py validate
```

### Task 1: repo-side publish-scope checker script

Context surface: the plan's Terms, this task, and the origin row docs/history/backlog/2026-11-08-release-publishes-tracked-ignored-files.md's Expected arm.

Files:
- `scripts/release_publish_scope_check.sh` *(new)*
- `scripts/test_release_publish_scope_check.py` *(new)*

Primary class anchors:
- `release_publish_scope_check.sh` in `scripts/release_publish_scope_check.sh`

- [x] Run then expect RED: `pytest scripts/test_release_publish_scope_check.py -q` fails before the script exists [class: REPOSITORY_TEST]
- [x] `release_publish_scope_check.sh` reads one path per line on stdin and exits 0 with no report lines for a clean list; report lines go to stdout, diagnostics to stderr [class: IMPLEMENTATION_REQUIRED]
- [x] Deny class 1: a stdin path that `git ls-files -i -c --exclude-standard` also reports produces `PUBLISH-SCOPE: <path> (tracked-but-ignored)` and exit 0; a tracked-ignored file NOT on stdin produces no line (the report is the delta intersection, never a repo-wide dump) [class: IMPLEMENTATION_REQUIRED]
- [x] Deny class 2: a stdin path that is a dated item file (`YYYY-MM-DD-*`) strictly inside a charter-empty directory and present at main's tip produces `PUBLISH-SCOPE: <path> (charter-empty-directory)` and exit 0; a deleted row under the directory, the charter README itself, and sibling directories (`completed-spring/`-shaped names) never match [class: IMPLEMENTATION_REQUIRED]
- [x] The charter-empty list is the checker's repo-side default constant (`docs/history/backlog/completed`) with a comment citing `docs/history/backlog/completed/README.md` as the rule's home; matching uses the directory component boundary, never a string prefix [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a failing or absent git repository, expects a nonzero tool-failure exit with no report lines emitted [class: IMPLEMENTATION_REQUIRED]
- [x] The checker applies the git_enumerate-class environment scrub around its git calls (unset `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_CONFIG*`, and the sibling selectors; `GIT_CONFIG_NOSYSTEM=1`; worktree `.gitignore` files still apply), mirroring `git_enumerate()` in `scripts/scan-public-hygiene.sh` [class: IMPLEMENTATION_REQUIRED]
- [x] `--selftest` arm exits 0 and covers both deny classes, the clean list, the deletion and README non-match arms, and a poisoned-env decoy; it pins its fixture repo's git config locally so ambient global config cannot flip a verdict [class: REPOSITORY_TEST]
- [x] Run then expect GREEN: the pytest suite passes with the fixture repo exercising both deny classes, the intersection-scoping negative, the constant-driven class 2 against a sibling-directory non-match, empty stdin (exit 0, no output), a delta path with a space and a non-ASCII byte (report line form asserted), the deletion and README non-match arms, pinned `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` fixture identity, and the tool-failure arm [class: REPOSITORY_TEST]
- [x] Commit: `release: add the publish-scope checker for tracked-ignored and charter-empty delta files` [class: IMPLEMENTATION_REQUIRED]

### Task 2: wire the checker into the release flow

Context surface: the plan's Terms, this task, and `agents/skills/release/SKILL.md` Steps 1-2 and Configuration.

Files:
- `scripts/release-rewrite.sh`
- `agents/skills/release/SKILL.md`

Primary class anchors:
- `Configuration (from facts document)` in `agents/skills/release/SKILL.md`
- `release-rewrite.sh` in `scripts/release-rewrite.sh`

- [x] `release-rewrite.sh` invokes the checker over the delta file list (`git diff --name-only --diff-filter=d` across `<remote>/main..main`, deletions excluded, piped to the checker) after the precondition re-checks and before the backup ref is created, in the ordinary and recovery paths; checker stdout is captured, never passed through [class: IMPLEMENTATION_REQUIRED]
- [x] Findings are echoed to stderr under a `PUBLISH SCOPE` banner naming each reported path and its deny class; the step never aborts on findings; the rewrite script's stdout continues to carry only the push-script path (its entire stdout contract) [class: IMPLEMENTATION_REQUIRED]
- [x] A checker nonzero exit prints one warning line naming the checker path and the exit status and continues; a configured checker path that does not exist prints one skip line and continues [class: IMPLEMENTATION_REQUIRED]
- [x] The release exit codes (0/1/2/3) and the privacy gate's contract are unchanged by the new step; `pytest scripts/test_release_skill_selftest.py` stays green [class: REPOSITORY_TEST]
- [x] `scripts/test_release_skill_selftest.py` gains the wiring-liveness cases: the fixture clone receives the checker, and one ordinary-path and one recovery-path case whose delta carries a force-added ignored path assert the stderr `PUBLISH SCOPE` banner names it, rc stays 0, and rewrite stdout remains exactly the push-script path [class: REPOSITORY_TEST]
- [x] `scripts/test_release_skill_selftest.py` gains the fail-open cases: a `RELEASE_PUBLISH_SCOPE_CHECKER` naming a nonexistent path asserts exactly one skip line, and a failing-stub checker asserts exactly one warning line, both with rc 0 [class: REPOSITORY_TEST]
- [x] `agents/skills/release/SKILL.md` gains the `RELEASE_PUBLISH_SCOPE_CHECKER` row in the Configuration table (repo-relative checker path resolved against the primary checkout, fallback `scripts/release_publish_scope_check.sh`) and one sentence in the Step 2 notes naming the stderr `PUBLISH SCOPE` banner among the output kept for the final summary [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `release: wire the publish-scope checker warning-only into the rewrite step` [class: IMPLEMENTATION_REQUIRED]

### Task 3: machinery-registry admission rows

Context surface: the plan's Terms, this task, and the existing row shapes in `scripts/machinery_registry.json`.

Files:
- `scripts/machinery_registry.json`

Primary class anchors:
- `machinery_registry.json` in `scripts/machinery_registry.json`

- [x] Entries row id `script:release_publish_scope_check.sh`, kind `script`, disposition `keep`, note carrying the warning-only posture and the review date 2026-12-08 [class: IMPLEMENTATION_REQUIRED]
- [x] The entries row carries `paths` naming `scripts/release_publish_scope_check.sh` (the registry's regrowth check requires every tracked script path in some entries row) and a witness object with class `incident` and ref this plan's path (tracked at landing) [class: IMPLEMENTATION_REQUIRED]
- [x] The entries note carries the admission fields: the incident (the 2026-11-08 published leak pair, dossier home this plan), expected catch frequency (every release whose pile carries a tracked-ignored or charter-empty file), and the false-positive cost (one report line per deliberately tracked path while warning-only; deletion events and the charter's own README never match) [class: IMPLEMENTATION_REQUIRED]
- [x] Removals row pre-registered for the same id with disposition `delete` and empty `paths` (a removals row naming a still-tracked path fails the inventory check; the removal target is named in the note instead) [class: IMPLEMENTATION_REQUIRED]
- [x] The removals note carries the promotion criteria (a true catch recorded in `scripts/gate_liveness_ledger.json` plus an operator-approved blocking flip with an explicit exemption mechanism), the sunset review date, witness class `incident`, and the durable-home sentence per the registry's pre-registered-row convention (plan archived at its landing; durable home: the plan's completed twin) [class: IMPLEMENTATION_REQUIRED]
- [x] The registry loads, `python3 scripts/machinery_inventory.py --check` exits 0, and the two rows match existing entries/removals shapes [class: REPOSITORY_TEST]
- [x] Commit: `machinery: register the release publish-scope check warning-only` [class: IMPLEMENTATION_REQUIRED]

### Task 4: convention alignment

Context surface: the plan's Terms, this task, and the sibling coordination row docs/history/backlog/2026-11-08-backlog-completed-dir-regrowth.md (coordinated, not absorbed).

Files:
- `AGENTS.md`
- `docs/maintenance/document-registry.md`
- `docs/maintenance/development_lessons.md`

Primary class anchors:
- `Commit & Pull Request Guidelines` in `AGENTS.md`
- `document-registry.md` in `docs/maintenance/document-registry.md`

- [x] The AGENTS.md witness-citation precedence clause is rewritten so a record citing a covered backlog row cites the covering plan's completed twin under `docs/history/plans/completed/`, and a `docs/history/backlog/completed/` twin is named a legacy state awaiting the sibling sweep, never a citation home for new records; this plan owns the clause edit, and the sibling row's licensing-text arm defers to it for this surface (recorded deconfliction) [class: IMPLEMENTATION_REQUIRED]
- [x] The `document-registry.md` header comment gains one sentence: new covered-backlog twins under `docs/history/backlog/completed/` are a legacy state, never a sanctioned landing destination; covered rows fold onto the covering plan and are deleted [class: IMPLEMENTATION_REQUIRED]
- [x] Lesson #4948's citation-precedence parenthetical (the `completed/` twin when one exists, otherwise the covering plan's completed twin) is amended to the new precedence so the machinery-registry witness re-pointing rule agrees with the rewritten AGENTS.md clause; no other lesson text changes [class: IMPLEMENTATION_REQUIRED]
- [x] The sibling row's owned surfaces stay untouched: the diff contains no change to `scripts/check_plan_origins_closed.py`, no file under `docs/history/backlog/completed/`, no `doc-hierarchy` edit, and no development_lessons.md change outside the #4948 parenthetical [class: REPOSITORY_TEST]
- [x] Commit: `docs: completed-home twins are legacy state; citation precedence resolves to the covering plan` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-08-release-publishes-tracked-ignored-files.md — covered; executed by this plan (execution landing cdbc0915c: the repo-side publish-scope checker with the tracked-ignored deny class wired warning-only into the rewrite step). Origin row deleted in this completion pass with the execution witness recorded in the landing commit.
- docs/history/backlog/2026-11-08-release-publishes-charter-empty-dir-rows.md — covered; executed by this plan (charter-empty dated-item deny class over the repo-side constant citing docs/history/backlog/completed/README.md as the rule's home). Origin row deleted in this completion pass.
- docs/history/backlog/2026-11-08-release-publish-scope-certification-residuals.md — covered; residuals 1-2 landed with the executed scope (core.quotepath=off plus -z raw-byte delta enumeration at the r1/r2 fix commits; the PUBLISH-SCOPE report-line literal asserted in the ordinary wiring case), residuals 3-7 were plan-prose identities superseded by the executed plan's own record. Origin row deleted in this completion pass.
