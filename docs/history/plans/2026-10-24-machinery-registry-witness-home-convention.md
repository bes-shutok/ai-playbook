# Plan: machinery-registry witness home convention

Authoring claim: docs/tmp/authoring-claims/2026-10-19-machinery-registry-witness-ref-rot.md (session sess-automation-bc3ff071-0200)
Plan review record: the staging series {reviews_dir}/2026-10-24-plan-review-machinery-registry-witness-home-convention-pd5c64f3c-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md
- docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md

Driving force: code-quality
Execution budget: 2.0h total, largest task 1.5h

## Terms

- witness reference: a path citing the record that motivated a machinery-registry admission or removal (the incident row), held in a JSON `ref` field, or a living backlog row's `Cluster:` pointer.
- durable home: the record that survives its landing: the covered row's `docs/history/backlog/completed/` twin when one exists, otherwise the covering plan's `docs/history/plans/completed/` twin; a keep entry's `witness.ref` must always resolve to a tracked path (never a commit hash; `scripts/machinery_inventory.py` enforces this), so the landing-commit home applies only to prose citations outside `witness.ref`.
- two-probe rule: a reference resolves only when both the filesystem check and `git cat-file -e HEAD:<path>` agree it exists.
- registry: `scripts/machinery_registry.json` (entries, removals, schema_version).
- covered-row rule: the Commit & Pull Request Guidelines bullet governing origin rows at landing: ad-hoc landings delete the row, landed plans archive it under `docs/history/backlog/completed/` with the covered flip.
- ref-field census: the census that parses the registry as JSON and probes only `ref` values, never path strings inside narrative note prose.
- origin row: a backlog row listed under Backlog origins that this plan's landing disposes per the covered-row rule.
- done-dirt region: the done skill's working-tree dirt surface whose valid-correction path landed on primary 2026-10-24 (commit 0eb7d617b).

## Why

Machinery-registry witness references and living `Cluster:` pointers cite records that their landings delete or archive, so every such citation rots at its own landing. The printed counts below are point-in-time context only; the merged base's fresh census at execution is the count source (Tasks 1-2 enforce this). At the r2 review HEAD the ref-field census showed roughly six dangling refs (one backlog, five plans paths, all with completed twins on disk) and a format-agnostic Cluster scan showed four dangling pointers in living rows, three outside this plan's original repair surface; the wider population is recorded in the task log at execution. The rot has already caused one blocking execution-review refusal.

## Gist & Examples

TLDR: name a durable home for witness references and repair every dangling one, for code-quality: citations survive the landings that delete or archive their targets.

Before: an admission entry cites `docs/history/backlog/<row>.md`; the landing that covers the row deletes it; the registry citation now dangles, and a reviewer who follows the witness finds nothing.

After: the same entry cites the row's `completed/` twin or the covering completed plan, and every living `ref` field and `Cluster:` pointer resolves under the two-probe rule, while historical note narration that must name a deleted row marks the deletion and names the durable home beside it instead of silently swapping the path.

## Outcome

Every `ref`-field witness reference in the registry and every `Cluster:` pointer in a living backlog row resolves, and new citations name records that survive their landing by convention.

- The dangling registry `ref` fields (backlog and plans paths) are re-pointed to their durable homes in one pass.
- The one living `Cluster:` pointer citing the retired staging-series-gate slug and the 2026-10-06 row's body citation are retargeted.
- The guidelines' covered-row bullet names the durable-home convention, so new admissions are born durable.

Gate delta: none. No gate, validator, fence, lock, ledger, schema field, or dispatch-pausing condition is added or removed; the change is convention wording plus a one-pass data repair, and the pins suite stays the pre-registered warning-only promotion path if the convention re-rots.

## Assumptions

- assume the convention is documentation-plus-repair, not a validator; basis: the origin row's Expected section prices a blocking gate behind the machinery admission protocol's witnessed-incident requirement, and its Why-not-fixed-now section defers the convention-versus-scan-arm design decision.
- assume the durable-home precedence (completed/ backlog twin, then covering plan's completed/ twin) matches the repo's surviving citation homes; basis: two-probe ref-field census 2026-10-24.
- assume archived completed-plan snapshots are historical and stand as written; basis: the 2026-10-09 origin row's Expected section.
- assume the executing tree is reconciled with primary main before Task 2 edits (primary landed 0eb7d617b after this plan's branch point, changing the done-dirt region); basis: risk round r1.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every `ref`-field witness reference and living `Cluster:` pointer resolves under the two-probe rule after the repair.
- maintainability: the convention is stated once in the guidelines' covered-row bullet and referenced, never duplicated per entry.

**Done when:**
- The ref-field census over the registry finds zero dangling refs (both backlog and plans paths, both probes agreeing), or refs parked per the Task 2 safety witness with the miss reported in the task log.
- The Cluster census (format-agnostic matcher, two-probe) finds zero unexplained dangling `Cluster:` pointers in the 2026-10-06 row, the only touched row still living at validation time (both origin rows exit the living set via the landing-time archive, and a Cluster line that already marks its referent's deletion is narration-compliant); the census's full output over all living rows is recorded in the task log, with pointers outside the touched rows reported as pre-existing rather than repaired.
- Registry note prose naming a deleted row marks the deletion and names the durable home beside it per the note-narration arm; the note-probe census output is recorded in the task log.
- `scripts/machinery_inventory.py --check` reports no failure that postdates this plan; the pre-existing failure baseline is recorded in the task log per Task 2's Inventory arm and non-ref failures are reported, not repaired.
- The guidelines' covered-row bullet names the durable-home convention for witness citations.

**Ship when:** none; local repository work only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `AGENTS.md` (the covered-row bullet in Commit & Pull Request Guidelines)
- `scripts/machinery_registry.json` (the re-pointed ref fields and the note-narration rewording arm)
- `docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md` (Cluster re-point and body citation)
- `docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md` (origin row disposition at landing)
- `docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md` (origin row disposition at landing)
- `docs/history/backlog/PLAN-PROMPTS.md` (origin listings re-point at landing)

**Tests:**
- none; the change is data and prose with probe-based validation.

**Plan-related extension:** review may re-point a reference the census missed when the two probes prove it dangles and a durable home is identifiable from disk evidence.

**Out of scope; reject unless plan-related:**
- citations inside `docs/history/plans/completed/` snapshots; reason: historical records stand as written per the origin row.
- any new scan script or validator; reason: rejected alternative, admission protocol.

## Validation Commands

```bash
python3 - <<'EOF'
import json, os, subprocess
reg = json.load(open('scripts/machinery_registry.json'))
refs = set()
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('ref','witness_ref') and isinstance(v, str): refs.add(v)
            else: walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(reg)
bad = [r for r in sorted(refs) if not os.path.exists(r) or subprocess.run(['git','cat-file','-e',f'HEAD:{r}'],capture_output=True).returncode]
print(len(refs), 'refs,', len(bad), 'dangling:', bad)
raise SystemExit(1 if bad else 0)
EOF
python3 - <<'EOF'
import os, re, subprocess, glob
def exists(p):
    if os.path.exists(p): return True
    return subprocess.run(['git','cat-file','-e',f'HEAD:{p}'],capture_output=True).returncode==0
bad = []
for f in glob.glob('docs/history/backlog/*.md'):
    if '/completed/' in f: continue
    for i, line in enumerate(open(f), 1):
        m = re.match(r"^(?:-\s+)?(?:\*\*)?Cluster:?(?:\*\*)?\s*(.*)$", line.strip())
        if not m: continue
        for pp in re.findall(r'docs/history/[\w./-]+\.md', m.group(1)):
            if not exists(pp): bad.append((f, i, pp))
touched = ('docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md',)
touched_bad = [b for b in bad if b[0] in touched]
print(len(bad), 'dangling Cluster pointers (out-of-scope ones reported as pre-existing):', bad)
raise SystemExit(1 if touched_bad else 0)
EOF
python3 - <<'EOF'
import json, os, re, subprocess
doc = json.load(open('scripts/machinery_registry.json'))
refvals = set()
def walkref(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('ref','witness_ref') and isinstance(v, str): refvals.add(v)
            else: walkref(v)
    elif isinstance(o, list):
        for v in o: walkref(v)
walkref(doc)
raw = open('scripts/machinery_registry.json').read()
note_paths = set(re.findall(r'docs/history/[\w./-]+\.md', raw)) - refvals
def exists(p):
    if os.path.exists(p): return True
    return subprocess.run(['git','cat-file','-e',f'HEAD:{p}'],capture_output=True).returncode==0
bad = [p for p in sorted(note_paths) if not exists(p)]
print(len(bad), 'dangling note-prose citations:', bad)
raise SystemExit(0)
EOF
python3 scripts/machinery_inventory.py --check; echo "inventory exit: $?"
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Land the durable-home convention wording

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `AGENTS.md`

- [ ] Amend the covered-row bullet in the Commit & Pull Request Guidelines section with one minimal clause: a record citing a backlog row as its witness cites the row's durable home (precedence completed/ backlog twin, then the covering plan's completed/ twin), and the same-commit tidy duty extends to witness re-points at removed or moved rows; tighten neighboring wording in the same edit so the bullet's growth is paid. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a future admission entry drafted against an open row, the amended bullet gives the author one rule that names the surviving record, so the citation is born durable and the witnessed execution-review refusal class cannot recur. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands ref-field census before the edit and record the pre-fix dangle count in the task log, asserting it matches the executing tree's fresh census rather than this plan's printed figures. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: name the durable-home convention for witness citations` [class: IMPLEMENTATION_REQUIRED]

### Task 2: One-pass repair of dangling references

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/machinery_registry.json`
- `docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md`
- `docs/history/backlog/2026-10-19-machinery-registry-witness-ref-rot.md`
- `docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md`
- `docs/history/backlog/PLAN-PROMPTS.md`

- [ ] Reconcile the executing tree with primary main before any registry edit (the done-dirt region moved on primary after this plan branched); re-derive the ref-field census on the merged base and treat each repair item conditionally: a citation already durable on the merged base is recorded as such and skipped. [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point the framework-callback `ref` fields (FOUR sites: two readability entries and two removals rows) to `docs/history/plans/completed/2026-10-15-framework-callback-readability-and-review-scope.md`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point every other dangling `ref` field the census names to its durable home, resolving each mapping at execution from the entry's own note and git history; the landing-deleted-unclaimed and review-staging-series refs were already durable at the 2026-10-24 census (verify on the merged base). [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-point the dangling `docs/history/plans/` ref fields the ref-field census's plans-path hits name (including the three live-entry witness refs `scripts/machinery_inventory.py --check` reports) to their `completed/` twins, all verified on disk at the 2026-10-24 census. [class: IMPLEMENTATION_REQUIRED]
- [ ] Note-narration arm: where the note-probe census names a registry note citation to a missing path, reword the sentence so it marks the deletion and cites the durable home as the surviving carrier (for example: deleted at landing; durable home: <completed path>); never substitute the path inside the historical claim; a citation recorded as pure historical narration keeps its path and gains the durable-home naming beside it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: a keep entry whose `witness.ref` has no surviving tracked-path home parks unchanged with the miss reported, never a commit hash (machinery_inventory rejects it) and never a guessed target; prose-only citations may fall back to the covering landing commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Retarget the one living `Cluster:` pointer citing the retired slug (the 2026-10-06 row) to `docs/history/plans/completed/2026-10-06-authoring-staging-preflight-gates.md`, and re-point that row's line-20 body citation to the same completed twin; leave the origin rows' self-descriptive prose untouched. [class: IMPLEMENTATION_REQUIRED]
- [ ] Landing-time arm (same change as this plan's own landing): archive both origin rows per the covered-row rule and re-point every citation of them in PLAN-PROMPTS.md (dispatch listings and prose) and the `Cluster:` pointers that cited them to the rows' completed/ twins, so this landing does not re-create the defect class it repairs. [class: IMPLEMENTATION_REQUIRED]
- [ ] Inventory arm: run `scripts/machinery_inventory.py --check` on the merged base before repairs, record its failure list as the pre-existing baseline in the task log, and disposition every non-ref failure as pre-existing and untouched; verify none of the baseline failures postdates this plan's change set. [class: REPOSITORY_TEST]
- [ ] Run the Validation Commands ref-field census, Cluster census, note-probe census, and inventory check; expect 0 dangling refs (or parks per the safety witness), 0 dangling Cluster pointers in the touched rows, note-probe output recorded, and no inventory failure postdating the change set. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: re-point dangling witness references to durable homes` [class: IMPLEMENTATION_REQUIRED]
