# Backlog: Validate public-repository captures beyond pattern-scan success

Status: done (docs/history/plans/completed/2026-10-01-backlog-capture-destination-ownership.md, main ad6f8c71)
Priority: medium
Workflow: backlog
Date: 2026-10-01
Class: fix-class
Origin class: witnessed-incident

## Problem

The misrouted company backlog records stated that `scan-public-hygiene --files` had passed, yet they retained company ticket, service, module, and internal document identifiers. The scan result was treated as proof that the records were suitable for the shared repository. A pattern scan only tests its configured deny patterns; it does not determine whether a document belongs in that repository or whether its project details are appropriate to publish. Partial masking of a package path also left the company context intact.

## Exact location

- `agents/skills/receiving-review/SKILL.md`, backlog capture hygiene wording and any public-repository destination path.
- `agents/skills/investigate/SKILL.md`, sanitization expectations for emitted tracked entries.
- Witness: the two 2026-09-30 reconcile follow-ups formerly in this repository's backlog; both were removed from here and preserved in the owning company project's backlog.

## Expected behavior

A passing configured-pattern scan is reported only as scan evidence, not as an ownership or publication-suitability decision. Before a company-origin finding can be recorded in a public or shared repository, remove company ticket identifiers, organization and service names, internal paths, and other identifying details while preserving only independently useful cross-project guidance. If sanitization would destroy the finding's actionable context, keep the record in its owning project repository.

## Suggested fix

Clarify the distinction between mechanical hygiene checks and destination suitability in the capture workflows. Add a review checklist or a narrow validation step for tracked backlog captures that catches company-specific identifiers in cross-project repositories, and provide neutral examples for what may be retained. Coordinate its scope with the existing hygiene-scan policy rather than broadening scan behavior implicitly.

## Severity and source reference

Severity: medium

Source: the two company-origin backlog records included an explicit hygiene-pass claim while retaining company ticket, service, module, and RFC details. Their original capture commit was `e6783f8190815b197dff4233818a6c138365dd1f`; the subsequent move returned the details to the owning project's repository.

## Why not fixed now

The records have been moved to the correct project. Updating the shared hygiene and capture contracts is separate work; the existing scan-scope item has explicit scope constraints and does not authorize silently changing the scanner's default coverage.

## Driving force

Driving force: privacy

Secondary force: reliability

## Dedup probe

Reviewed the existing hygiene scan-scope backlog item and current receiving-review/investigate capture instructions. The existing item addresses scanner coverage and residue in tracked docs; it does not prevent an agent from treating a pattern-scan pass as proof of project ownership or complete anonymization. Keep this as a complementary capture-policy item.

## Trigger

Before relying on a public-hygiene scan result as the only validation for a company-origin backlog capture in a cross-project repository.
