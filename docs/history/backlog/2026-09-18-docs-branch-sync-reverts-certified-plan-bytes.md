# Backlog: docs-branch sync can commit an older plan shape over a certified one, manufacturing stale-digest gate failures

Status: open
Priority: high
Workflow: backlog

## Observed vs expected

2026-09-18: executing a plan whose pre-execution readiness gate had been certified
(r7, digest `a9344f3e...`) failed the Step 0.5 gate with a stale `source_digest`.
Per-commit hashing of the plan blob showed the certified two-half pin shape existed
only on one merged-branch lineage; main's lineage carried the pre-rebase simple
shape, a docs-branch sync commit (`docs: update from docs`) re-exported that older
shadow-tree copy over main, and a later peer execution applied its three content
hunks on top of the stale base. Executing main's bytes would have re-introduced a
known design collision the certified round had resolved. Expected: a sync that
would change a plan file's bytes relative to the latest certified digest (sidecar
under the reviews dir) either refuses, warns loudly at sync time, or records the
certified-digest mismatch so the next gate failure is explained by history rather
than requiring per-commit blob archaeology.

## Reproduction evidence (trimmed)

- Certified plan bytes at commit A on branch B (merged content never reached main).
- Main lineage: commit C carries the older shape; sync commit D sets the plan blob
  equal to C's (the shadow-tree copy was stale relative to B).
- Later commit E appends unrelated hunks to the stale base.
- `plan_readiness.py <plan>` at execution time: `readiness FAILED: sidecar
  source_digest is stale`.

## Environment

- Runtime: unattended scheduled execution session; repo with gitignored
  `docs/` shadow tree synced to an orphan `docs` branch by the docs-branch skill.
- Date: 2026-09-18. Repo copy of the skills; deployed runtime copies in use.

## Suspected root area

`agents/skills/docs-branch/SKILL.md`: the add-only sync commits shadow-tree bytes
without comparing plan files against their latest review sidecar digest, so a stale
shadow copy can silently outrank a certified one on the tracked branch. A
sync-time digest check (or a gate-time lineage pointer in the failure message)
would close the surface. Related family: the gate itself worked as designed; the
defect is that recovering requires hashing the blob across every commit that
touched the file to locate the certified bytes.
