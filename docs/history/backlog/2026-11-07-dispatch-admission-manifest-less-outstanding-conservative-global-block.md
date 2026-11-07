# Backlog: dispatch admission conservative verdict over manifest-less outstanding runs globally blocks the exec lane

- filed: 2026-11-07
- driving force: efficiency
- cluster: dispatch-admission
- cluster: docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md
- status: open

## Symptom (witnessed 2026-11-07 ~17:35Z, interactive exec session)

The execution lane stood down 0/1 with a fully dispatchable head candidate
(`docs/history/plans/2026-11-06-doing-code-review-staging-doc-scaffold-pointer.md`,
work verified NOT landed on main). `scripts/dispatch_admission.py` REFUSED
(`OUTCOME: fail`): two live peer exec runs
(`doc-registry-row-edit-validator-timing`, claim fresh 16:52Z;
`test-suite-runtime-reduction`, claim fresh 16:36Z) were mid-execution and
had minted no done-setup run manifests yet. The consult models no evidence
source for such a run: `--outstanding-without-manifest` takes the
conservative "treated as intersecting" verdict (module docstring, the
degenerate-inputs clause), and the verdict is global — every candidate of
either lane is blocked, not just target-adjacent ones. The lane can stay
blocked for the whole multi-hour duration of any peer run that mints its
manifest only at done-setup (end of run), which is the normal shape.

## Investigation

- The consult's outstanding-run inputs are manifest-or-nothing
  (`scripts/dispatch_admission.py` header, `OutstandingRun.owned_paths is
  None` path in `check_admission`). It cannot consume a claim file or a
  covering-plan `Files:` list for an outstanding run, although the same
  plan-derived derivation exists for the candidate side
  (`owned_paths_from_plan`).
- The designed fix already exists as an authored, certified, UNEXECUTED
  plan: `docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md`
  (landed 1933ba5f4, r5-certified, execution pending). It seeds a
  claim-keyed admission record at the execution-claims home from the
  covering plan's `Files:` lists at claim take, merges monotone at done
  boundaries, and has the consult read it beside each done-session
  manifest as same-label operands, with evidence-strict reads.
- Until that plan executes, every exec/authoring turn that surveys while a
  peer exec run is mid-flight inherits the same conservative refusal and
  defers (witnessed repeatedly in the scheduler state file 2026-11-06/07).

## Ask

Execute the `dispatch-admission-outstanding-manifest-recovery` plan (it is
the fix and sits in the open exec queue); until it lands, the conservative
global block stays accepted behavior — no gate edit is requested. If that
plan's execution is itself blocked by this same verdict when peers are
live, admit it as the sanctioned recovery exception (its own owned paths
are admission machinery, disjoint from most plan work) or execute it in a
peer-free window.

## Relationship

- covering plan: docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md (fix vehicle, execution pending)
- origin machinery: docs/history/plans/2026-11-04-parallel-execution-landing-serialization-blockers Task 1
