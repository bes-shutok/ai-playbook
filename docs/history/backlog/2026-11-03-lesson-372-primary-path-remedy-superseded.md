# Backlog: lesson #372's primary-path remedy superseded by the twin exemption

Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Class: fix-class
Driving force: consistency

## Problem

Lesson #372 in `docs/maintenance/development_lessons.md` ("A Path-Equality Gate Self-Exemption Needs the Primary-Path Declaring Operand After a Certification Checkpoint") instructs resolving the declaring operand in the primary checkout so the path-equality exemption matches, and treating a worktree-relative declaring operand as suspect whenever a checkpoint twin exists. The coverage gate's self-exemption now also exempts a byte-identical twin whose parent directory is exactly the active plans directory (plan docs/history/plans/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md), so a worktree-relative run passes on the checkpoint-twin shape and the title's "Needs the Primary-Path Declaring Operand" no longer holds for this gate. The Rule's general shape and the Why's witnessed history stay valid; only the remedy sentence and title assert the old shape as current.

Deferred from the run's code review r1 (record `.ai-playbook/reviews/2026-11-03-coverage-gate-checkpoint-twin-self-exemption-code-review-r1.md`, finding 8, pattern documentation#prose-outdated-doc): the lessons corpus is out of the plan's scope and is harvested by the learn flow.

## Expected

A dated supersession witness on #372 recording the new exemption shape.

## Suggested change

Append to #372's Why (via the learn flow, following the #373 remedy-arm witness pattern): "Superseded for this gate 2026-11-03: the coverage gate's self-exemption now also exempts a byte-identical twin whose parent directory is exactly the active plans directory (plan docs/history/plans/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md), so the primary-path operand is no longer required there; the canonicalize-the-operand arm remains for gates whose exemption is still path-only."

Cluster: docs/history/backlog/2026-11-03-twin-plan-note-resolution-site-drift.md (same landing's deferred doc-fidelity captures)
