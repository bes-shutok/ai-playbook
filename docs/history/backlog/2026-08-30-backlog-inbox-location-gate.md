# Backlog: mechanical gate rejecting backlog-inbox files outside `{backlog_dir}`

Status: open
Workflow: backlog
Source: 2026-08-30 session (invented-backlog-destination incident on a private
service repo, ticket id elided; receiving-review Backlog capture)
Severity: Low (hardening follow-up, non-blocking)
Anchors: agents/skills/receiving-review/SKILL.md (Backlog capture destination
list), agents/skills/bootstrap-ai-playbook/SKILL.md (backlog key discovery),
agents/skills/doc-hierarchy/SKILL.md (Backlog lifecycle)
Decision: user-deferred same session, 2026-08-30 (optional second line of
defense behind the skill hardening)

## Problem

When `{backlog_dir}` was unresolved on a target repo (facts lacked
`backlog_dir` / `backlog_completed_dir`), review and done agents invented
`docs/maintenance/<TICKET>-*-deferred-backlog.md` as a backlog inbox, one
file per review round. The skill-level fix landed 2026-08-30: `receiving-review`
**Backlog capture** now fails closed (bootstrap recovery, then ask; never
`docs/maintenance/` or `docs/tmp/`), `bootstrap-ai-playbook` resolves or
creates the backlog home, and `doc-hierarchy` documents the lifecycle.
Nothing mechanical rejects the write, so a non-compliant agent can still
invent a durable-looking location and no gate fails.

## Suggested fix

Add a repo-agnostic validator (candidate home: `scripts/`, wired into the
hygiene scan or the `done` gates) that rejects newly tracked files matching
backlog-inbox shapes outside `{backlog_dir}`: filename contains `backlog` or
`deferred` (case-insensitive) under `docs/maintenance/`, `docs/architecture/`,
or `docs/tmp/`, or any `*deferred*backlog*` filename outside the resolved
`{backlog_dir}`. Needs a breadth decision first: content-based "mentions
backlog" patterns would false-positive on legitimate Layer 2 docs that
reference the backlog workflow, so the gate should key on filename shape and
location, not content.

## Why not now

Second line of defense behind the 2026-08-30 skill hardening, which addresses
the root cause (missing facts keys plus an invented fallback). The validator
needs a design decision on pattern breadth and gate placement (hygiene scan
vs done hook vs per-repo validator copy) before implementation; folding a
mechanical gate into the same pass would have mixed a wording/lifecycle fix
with new gate surface.
