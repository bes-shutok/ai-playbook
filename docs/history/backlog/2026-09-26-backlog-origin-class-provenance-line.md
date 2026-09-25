# Backlog: require an Origin class provenance line on newly created backlog items

Status: open
Priority: high
Scope: agents/skills/receiving-review/, agents/skills/learn/, agents/skills/maintenance/ (shared skills under agents/skills/)
Workflow: backlog
Source: owner directive 2026-09-26 (source-class ordering: consumer-project failure feedback outranks self-serving improvements; external items carry a company-versus-pet project-family tag)
Origin class: self-serving
Class: real (owner-directed process change; witness: the 2026-09-26 deferred-corpus triage had to reconstruct provenance by reading every item body, and the promotion pass recorded the classification only in ad-hoc remarks on promoted items)

## Problem

Backlog items do not record where the need came from. The 2026-09-26 direction triage had to read all 91 deferred item bodies to separate consumer-project failure feedback from self-serving improvements before it could order urgencies, and the promotion pass then recorded that classification in `Promoted:` and `Consumer urgency:` remark lines that only the 19 promoted items carry. Capture time is the cheap moment to record provenance; triage time is the expensive one. The same gap repeats every future triage unless capture records it.

## Fix direction

1. `agents/skills/receiving-review/SKILL.md` (Backlog capture required content; the item-format SOT): require an `Origin class:` header line on every newly captured item, exactly one value:
   - `Origin class: self-serving`: the failure or improvement was witnessed on the skills repo's own runtime; no consumer project is involved.
   - `Origin class: consumer-feedback (company)`: witnessed in a company project that consumes these skills.
   - `Origin class: consumer-feedback (pet)`: witnessed in the owner's personal pet projects that consume these skills.
   Next to the existing `Consumer urgency:` rule, state the ordering semantics: at equal priority, consumer-feedback outranks self-serving, and the company/pet tag names which project family's priority profile (guidelines rule 68) consults when a shared-skill fix trades one consumer family against the other. A consumer-feedback item that also meets the existing Consumer urgency conditions still carries that line; the two lines compose (provenance plus never-profile-deferred), neither replaces the other.
2. `agents/skills/learn/SKILL.md` (Step 1.8 skill-usage captures) and `agents/skills/maintenance/SKILL.md` (the friction-audit lane's new-item duty and any directive-filing surface): require the same line; these surfaces already follow receiving-review's capture content by reference, so extend the reference, never restate the vocabulary.
3. `agents/skills/maintenance/SKILL.md` Step 1 survey and Step 3 selection: record the origin class beside the existing class token in the decision_reason token shape (`<item-basename>:origin=<self-serving|consumer-company|consumer-pet|unknown>`); selection orders consumer-feedback items before self-serving items within the same priority group; a missing line is judged from the item body at survey time and recorded in the token, never by editing the item. No bulk retrofit of the existing corpus; items gain the line on next capture or touch.
4. Non-capture surfaces (execute-plan off-plan capture, review-loop, review-reconciliation) already route through receiving-review's Backlog capture and need no edit; verify that claim during authoring with a grep before widening scope.

## Acceptance

- A capture dry run (one sample review finding routed to Backlog capture) produces the `Origin class:` line with the correct value, and the receiving-review required-content list names all three values with the ordering semantics.
- The maintenance survey token carries the origin class, and a mixed-priority selection orders consumer-feedback items first while an absent line yields `origin=unknown` judged from the body.
- No existing backlog item is edited by the change; the corpus gains lines only through new captures and natural touches.
