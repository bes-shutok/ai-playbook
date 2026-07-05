#!/usr/bin/env bash
# Cursor lessons-recall adapter (best-effort sessionStart one-shot).
#
# LIMITATION (documented in README): Cursor cannot silently inject context on
# every prompt the way Claude UserPromptSubmit does. Cursor fires a sessionStart
# hook ONCE per session, so this adapter emits a COMPACT FAMILY INDEX built
# directly from the corpus at session start, rather than per-prompt recall. The
# family index is built INLINE in this adapter (no shared helper): iterate the
# corpus via lessons_corpus.iter_lessons and pick the lowest-numbered lesson per
# present family, producing one line per family as a recall menu the agent can
# grep later.
#
# Prompt extraction: Cursor's sessionStart payload may carry a `.prompt` or be
# empty; this adapter does NOT depend on it (it builds the index regardless).
#
# Session model (r10-B1): SID is derived VERBATIM as
#   SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
# The helper returns CLAUDE_CODE_SESSION_ID or CURSOR_SESSION_ID
# or "" (Claude precedence when both env vars are set).
#
# Bridge dependency (v2, optional): per-tab session isolation requires
# cursor-session-bridge.sh registered FIRST in the sessionStart array so
# Cursor exports .session_id into CURSOR_SESSION_ID for later
# hooks in the same composer tab. Without the bridge installed, session_channel
# returns empty for Cursor -> this adapter OMITS `--session-id` -> core keys
# `no-session` + FULL window (v1 steady state, unchanged). With the bridge,
# each tab gets a distinct session hash for dedup state and skill-gate markers.
#
# The session args are passed to the index-builder only for path-key
# consistency of the per-(project,session) state file used by the core's dedup
# on later calls; this one-shot itself emits the index without consulting
# dedup state (the index is a menu, not a de-duplicated reminder).
#
# Exit 0 ALWAYS.
set -u

CORE_DIR="$HOME/.ai-playbook/scripts"

# Derive the session id VERBATIM via the shared helper subprocess.
SID="$(python3 "$CORE_DIR/session_channel.py")"

# Build the compact family index INLINE: iterate lessons_corpus.iter_lessons
# over the user-level + project corpora, pick the lowest-numbered lesson per
# present family. The corpora are resolved via facts_paths.user_corpus_path
# (user-level) and the cwd-relative project corpus convention. The project
# corpus RELATIVE path is imported from the lessons_recall core
# (PROJECT_CORPUS_REL) so the path constant has ONE home (Family D); the
# family-selection logic itself is a one-shot index that the core has no
# equivalent mode for (the core classifies a single prompt and emits a
# reminder; it does not enumerate all families), so it stays inline here.
#
# stderr is discarded; never fail.
index="$(python3 -c '
import os, sys
from pathlib import Path
# Resolve the REPO scripts dir via the symlinked core (the cores siblings
# facts_paths/lessons_corpus are NOT symlinked into ~/.ai-playbook/scripts/;
# only session_channel.py and lessons_recall.py are). The resolved parent of
# the lessons_recall.py symlink IS the repo scripts dir where the siblings
# live.
core_link = Path(os.path.expanduser("~/.ai-playbook/scripts/lessons_recall.py"))
scripts_dir = str(core_link.resolve().parent)
sys.path.insert(0, scripts_dir)
import facts_paths
import lessons_corpus
import lessons_recall

seen = {}  # family -> (number, title)
candidates = []
user_corpus = facts_paths.user_corpus_path(Path.cwd())
if user_corpus is not None:
    candidates.append(user_corpus)
# Single source for the project-corpus relative path (r1-M11): import
# PROJECT_CORPUS_REL from the core instead of re-hardcoding the literal here.
project_corpus = Path.cwd() / lessons_recall.PROJECT_CORPUS_REL
candidates.append(project_corpus)

for path in candidates:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        continue
    for L in lessons_corpus.iter_lessons(text):
        for fam in L.tags:
            if fam in lessons_corpus.VALID_FAMILIES:
                if fam not in seen or L.number < seen[fam][0]:
                    seen[fam] = (L.number, L.title)

# Emit one line per family, sorted by family letter.
lines = []
for fam in sorted(seen):
    n, title = seen[fam]
    lines.append(f"Family {fam}: #{n} {title}")
sys.stdout.write("\n".join(lines))
' 2>/dev/null || true)"

if [ -n "$index" ]; then
    # Cursor envelope shape mirrors the flat additionalContext form. The index
    # is injected as the additionalContext value via json.dumps dict
    # construction.
    printf '%s' "$index" | python3 -c 'import json,sys
idx = sys.stdin.read()
if idx.strip():
    sys.stdout.write(json.dumps({"additionalContext": idx}))
'
fi
exit 0
