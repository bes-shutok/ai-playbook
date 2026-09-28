# Plans GREEN-simulation insertions must be extracted from the plan's prescribed spans, never hand-rebuilt

- **Filed:** 2026-09-30
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** code-quality; secondary simplicity
- **Source:** learn Step 1.8 capture, 2026-09-30, from a plan-authoring session whose validation-block count gate pinned a value the plan's own prescribed texts could never produce. The authoring-time GREEN simulation was built by re-typing the planned insertions from memory of the fold; one unprescribed summary sentence crept in, the count gate pinned the simulated 6, and a faithful landing could only ever read 5. Five independent review workers derived the same 5 in the next round, costing a blocking review round, a re-pin, and a re-simulation.

## Problem

The plans authoring rules (agents/skills/plans/SKILL.md, "Validation Commands (authoring rules)") already require executing gates in both polarities (rule 41) and simulating the duplicate direction (rule 36), and rule 24 bans hand-written expectations for transforms. None of them pins the fidelity of the simulation's INPUT: nothing forbids building the scratch-tree insertions by hand rather than extracting the quoted spans from the plan file itself. A hand-rebuilt simulation diverges from the prescription silently, and every count expectation derived from it is wrong on arrival in a way no present-tense gate can catch, because the gate reads the simulation, not the plan.

## Expected behavior

- One authoring rule (or an extension of rule 36): the GREEN-polarity simulation's inserted bytes are extracted mechanically from the plan's own prescribed spans (for example, programmatic extraction of each task's quoted insertion text), never re-typed from recall; a simulation whose inserted bytes are not byte-identical to a span the plan prescribes is void and its derived expectations are unpinnable.
- The extraction step is cheap (a few lines of script over the plan text) and removes the recert round this defect class costs.

## Possibility space and simplifications

- **Recommended: one authoring rule, prose only.** The rule extends the existing both-polarity duty; no script, hook, or validator is created.
- **Rejected: a bundled extraction script.** Machinery; the extraction is three lines of the author's own scripting at authoring time, and a script would need maintenance against plan-format drift.
- **Rejected: banning hand-built simulations outright.** Ad-hoc behavioral probes stay legitimate (rule 27); only gate EXPECTATION derivation binds to prescribed bytes.

## Acceptance

- Plans whose validation blocks pin counts derived from a simulation record, beside the simulation, that the inserted bytes were extracted from the plan's prescribed spans (or carry the extraction command); the C9-class defect (simulation-vs-prescription divergence) is caught at authoring time instead of costing a review round.
- Fix-class disposition: the block that disappears is the recert round; no new refusal path is added to any runtime or review flow.
