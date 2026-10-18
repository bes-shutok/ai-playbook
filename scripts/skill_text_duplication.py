#!/usr/bin/env python3
"""Machinery admission test (read-only; never gates):

skill_text_duplication.py - read-only quantified substrate for the repository
guidelines' skill text anti-growth rules (the Part 2 method of
docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md).

- Concrete incident: the 35-commit landing ratchet with exactly one 64-byte
  shrink and the roughly 89K-token per-turn doctrine load
  (docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md).
- Expected catch frequency: a weekly rider read plus per-cycle consolidation
  reads; docs/maintenance/recurring-tasks/weekly-measurement-rider.md is the
  cadence home.
- False-positive cost: zero blocking; the script never gates, findings are
  data for the consumers (the doc-hygiene row's standing review arm and the
  byte-budget gate's growth-telemetry consumer).
- Sunset: if no consumer reads the report across six consecutive weekly rider
  windows, the script and its machinery-registry row
  (skill-text-duplication-report) are removed, the row moving to the
  registry's removals record with this sunset as the witness.

Method (Part 2): per Markdown file, normalize text (lowercased, punctuation
stripped, whitespace collapsed), build 10-word shingles, and report the
repeated-span percentage (the share of words lying in a shingle that occurs at
least twice in the file), the exact duplicated sentences of 60 or more
normalized characters with counts, and per file pair the count of distinct
shared 10-word shingles. Deterministic: same tree, byte-identical output.

The script writes nothing but stdout. Exit contract: `OUTCOME: pass` and
exit 0 on any completed analysis (findings are data, never failures);
`OUTCOME: fail` and exit 1 only on usage or unreadable-input errors.
"""
import json
import os
import re
import sys
from collections import Counter

SHINGLE = 10
MIN_SENT = 60
USAGE = (
    "usage: skill_text_duplication.py [--json] [--top N] [PATH ...]\n"
    "  PATH   a Markdown file or a directory to walk (default: agents/skills/);\n"
    "         docs/history/ and synced/ subtrees are always excluded\n"
    "  --top  bound the reported duplicated sentences and file pairs (default 10)\n"
)


def fail(message):
    sys.stdout.write("error: %s\nOUTCOME: fail\n" % message)
    return 1


def parse_args(argv):
    top = 10
    as_json = False
    paths = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            as_json = True
        elif a == "--top":
            if i + 1 >= len(argv):
                return None, None, None, "--top requires a value"
            try:
                top = int(argv[i + 1])
            except ValueError:
                return None, None, None, "--top expects an integer, got %r" % argv[i + 1]
            if top < 0:
                return None, None, None, "--top must be non-negative"
            i += 1
        elif a in ("-h", "--help"):
            return "help", None, None, None
        elif a.startswith("-"):
            return None, None, None, "unknown argument: %s" % a
        else:
            paths.append(a)
        i += 1
    return "run", as_json, top, (paths or ["agents/skills/"])


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def collect_md_files(paths):
    """Expand inputs to a sorted list of Markdown file paths (repo-relative
    when under the repo, else as given), excluding docs/history/ and synced/."""
    out = set()
    for p in paths:
        if os.path.isdir(p):
            top = os.path.abspath(p)
            for root, dirs, files in os.walk(top):
                kept = []
                for d in dirs:
                    rel = os.path.relpath(os.path.join(root, d), top).replace(os.sep, "/")
                    parts = rel.split("/")
                    if "synced" in parts or (parts[:2] == ["docs", "history"]):
                        continue
                    kept.append(d)
                dirs[:] = kept
                for f in files:
                    if f.endswith(".md"):
                        out.add(os.path.join(root, f))
        elif os.path.isfile(p):
            if not p.endswith(".md"):
                return None, "%s is not a Markdown file" % p
            out.add(p)
        else:
            return None, "unreadable input path: %s" % p
    return sorted(out), None


def analyze_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    norm = normalize(raw)
    words = norm.split() if norm else []
    shingles = Counter(
        tuple(words[i:i + SHINGLE]) for i in range(0, len(words) - SHINGLE + 1)
    ) if len(words) >= SHINGLE else Counter()
    repeated = sum(c for s, c in shingles.items() if c >= 2) if shingles else 0
    # words lying in at least one repeated shingle occurrence-window: a word
    # index is covered if it falls inside any shingle window that occurs >=2 times
    covered = set()
    if shingles:
        for i in range(0, len(words) - SHINGLE + 1):
            if shingles[tuple(words[i:i + SHINGLE])] >= 2:
                covered.update(range(i, i + SHINGLE))
    pct = (len(covered) / len(words) * 100.0) if words else 0.0
    # split raw text into sentences on terminal punctuation BEFORE normalizing
    # (normalization strips the punctuation the splitter needs)
    raw_sentences = [s for s in re.split(r"(?<=[.!?])\s+", raw) if s.strip()] if raw.strip() else []
    dup = Counter()
    for rs in raw_sentences:
        ns = normalize(rs)
        if len(ns) >= MIN_SENT:
            dup[ns] += 1
    dup = {t: c for t, c in dup.items() if c >= 2}
    return {
        "path": path,
        "words": len(words),
        "repeated_span_pct": round(pct, 1),
        "duplicated_sentences": sorted(dup.items()),
        "_shingles": set(shingles),
    }


def main(argv):
    mode, as_json, top, paths_or_err = parse_args(argv)
    if mode == "help":
        sys.stdout.write(USAGE + "OUTCOME: pass\n")
        return 0
    if mode is None:
        return fail(paths_or_err)
    files, err = collect_md_files(paths_or_err)
    if err:
        return fail(err)
    results = [analyze_file(f) for f in files]
    for r in results:
        if r["words"] < SHINGLE or not r["_shingles"]:
            r["repeated_span_pct"] = 0.0
    pair_rows = []
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            shared = len(results[i]["_shingles"] & results[j]["_shingles"])
            if shared:
                a, b = sorted([results[i]["path"], results[j]["path"]])
                pair_rows.append({"path_a": a, "path_b": b, "shared_shingles": shared})
    pair_rows.sort(key=lambda r: (r["path_a"], r["path_b"]))
    files_out = [
        {
            "path": r["path"],
            "words": r["words"],
            "repeated_span_pct": r["repeated_span_pct"],
            "duplicated_sentences": r["duplicated_sentences"][:top],
        }
        for r in sorted(results, key=lambda r: r["path"])
    ]
    if as_json:
        payload = {"files": files_out, "pairs": pair_rows[:top] if top else pair_rows}
        # declared placement deviation (done-lock precedent): --json stdout is
        # machine-consumed, so the final OUTCOME line rides stderr there
        sys.stdout.write(json.dumps(payload, sort_keys=True, indent=1) + "\n")
        sys.stderr.write("OUTCOME: pass\n")
    else:
        for f in files_out:
            sys.stdout.write(
                "%s: words=%d repeated_span_pct=%.1f duplicated_sentences=%d\n"
                % (f["path"], f["words"], f["repeated_span_pct"], len(f["duplicated_sentences"]))
            )
            for text, count in f["duplicated_sentences"][:top]:
                sys.stdout.write("  x%d %s\n" % (count, text))
        pairs = pair_rows[:top] if top else pair_rows
        if pairs:
            sys.stdout.write("cross-file shared 10-gram intersections:\n")
            for pr in pairs:
                sys.stdout.write("  %s <-> %s: %d\n" % (pr["path_a"], pr["path_b"], pr["shared_shingles"]))
    if not as_json:
        sys.stdout.write("OUTCOME: pass\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
