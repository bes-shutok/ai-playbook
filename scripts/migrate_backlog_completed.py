#!/usr/bin/env python3
"""Fold-then-delete migration helper (backlog completed archive policy).

Maps each dated per-item file under the completed backlog inbox to its
disposition home (a completed plan under the plans completed dir, or the
--self-host plan), appends one disposition bullet there, licenses every
mutation with the registry's `user-approved <date>:` audit-note form, and
deletes the per-item file. Dry-run by default; --apply mutates.
"""

import argparse
import os
import re
import sys

STOP_WORDS = {"a", "an", "and", "or", "the", "of", "to", "in", "on", "for", "with"}
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
SECTION = "## Disposition of migrated backlog items"
COLUMNS = 9


def strip_date_prefix(name):
    return DATE_PREFIX_RE.sub("", name[:-3] if name.endswith(".md") else name)


def tokenize(stem):
    return [t for t in stem.lower().split("-") if t and t not in STOP_WORDS]


def item_date(name):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", name)
    return (m.group(1) + m.group(2)) if m else ""


def read_lines(path):
    with open(path) as f:
        return f.read().splitlines(True)


def write_lines(path, lines):
    with open(path, "w") as f:
        f.writelines(lines)


def registry_rows(lines):
    """Yield (index, cells) for table rows; cells exclude the outer pipes."""
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and "---" not in s:
            cells = [c.strip() for c in s[1:-1].split("|")]
            if len(cells) == COLUMNS and cells[0] != "identity":
                yield i, cells


def find_root(start):
    root = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(root, ".git")):
            return root
        parent = os.path.dirname(root)
        if parent == root:
            return os.path.abspath(start)
        root = parent


def rel(path, root):
    return os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")


class Registry:
    def __init__(self, path):
        self.path = path
        self.lines = read_lines(path)
        self.root = find_root(os.path.dirname(path))

    def rows(self):
        return list(registry_rows(self.lines))

    def row_for_src_suffix(self, name):
        suffix = "/" + name
        for i, cells in self.rows():
            if cells[5] == name or cells[5].endswith(suffix):
                return i, cells
        return None

    def identity_taken(self, identity):
        return any(cells[0] == identity for _, cells in self.rows())

    def next_identity(self, base, mmdd):
        if not self.identity_taken(base):
            return base
        cand = "%s-%s" % (base, mmdd) if mmdd else base + "-x"
        if not self.identity_taken(cand):
            return cand
        return "%s-backlog" % cand

    def append_row(self, identity, src_rel, date, audit):
        row = "| %s | no | completed | %s | executed | %s |  |  | %s |\n" % (identity, date, src_rel, audit)
        self.lines.append(row if self.lines[-1].endswith("\n") else row)

    def set_audit(self, index, cells, note):
        line = self.lines[index]
        lead = line[: len(line) - len(line.lstrip())]
        trailing = "\n" if line.endswith("\n") else ""
        cells = list(cells)
        cells[8] = note
        self.lines[index] = lead + "| " + " | ".join(cells) + " |" + trailing


def append_bullet(plan_path, bullet):
    lines = read_lines(plan_path)
    if any(bullet.strip() == l.strip() for l in lines):
        return False
    text = "".join(lines)
    if SECTION in text:
        idx = next(i for i, l in enumerate(lines) if l.strip() == SECTION)
        insert = idx + 1
        while insert < len(lines) and lines[insert].strip().startswith("-"):
            insert += 1
        lines.insert(insert, bullet)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n%s\n\n%s" % (SECTION, bullet)
        write_lines(plan_path, text.splitlines(True))
        return True
    write_lines(plan_path, lines)
    return True


def match_item(item_name, plan_names):
    """Return (destination_name or None, tied bool)."""
    tokens = set(tokenize(strip_date_prefix(item_name)))
    best = []
    best_score = 1
    for plan_name in plan_names:
        score = len(tokens & set(tokenize(strip_date_prefix(plan_name))))
        if score > best_score:
            best_score = score
            best = [plan_name]
        elif score == best_score and score >= 2:
            best.append(plan_name)
    if not best:
        return None, False
    tied = len(best) > 1
    return sorted(best)[0], tied


def build_report(inbox, plans_dir, self_host, overrides):
    plan_names = sorted(n for n in os.listdir(plans_dir) if n.endswith(".md"))
    items = sorted(n for n in os.listdir(inbox) if n.endswith(".md"))
    lines = []
    for item in items:
        stem = strip_date_prefix(item)
        if stem in overrides:
            lines.append("override: %s -> %s" % (item, overrides[stem]))
            continue
        dest, tied = match_item(item, plan_names)
        if dest is None:
            lines.append("self-host: %s -> %s" % (item, os.path.basename(self_host)))
        else:
            tag = " [tie]" if tied else ""
            lines.append("matched%s: %s -> %s" % (tag, item, dest))
    return lines


def parse_overrides(path):
    out = {}
    if not path:
        return out
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                raise ValueError("bad overrides line: %r" % line)
            out[parts[0]] = parts[1]
    return out


def resolve_destination(dest_rel, plans_dir):
    cands = [dest_rel, os.path.join(find_root(os.path.dirname(plans_dir)), dest_rel),
             os.path.join(os.path.dirname(plans_dir), dest_rel)]
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plans-dir", required=True)
    ap.add_argument("--backlog-completed-dir", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--self-host", required=True)
    ap.add_argument("--overrides")
    ap.add_argument("--report")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date", default=None)
    args = ap.parse_args(argv)
    date = args.date or __import__("datetime").date.today().isoformat()

    try:
        overrides = parse_overrides(args.overrides)
    except ValueError as exc:
        print("usage error: %s" % exc, file=sys.stderr)
        return 2

    inbox, plans_dir = args.backlog_completed_dir, args.plans_dir
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        write_lines(args.report, [l + "\n" for l in build_report(inbox, plans_dir, args.self_host, overrides)])

    if not args.apply:
        return 0

    reg = Registry(args.registry)
    plan_names = sorted(n for n in os.listdir(plans_dir) if n.endswith(".md"))
    items = sorted(n for n in os.listdir(inbox) if n.endswith(".md"))

    # Resolve every mapping and validate override destinations BEFORE mutating.
    mappings = []
    for item in items:
        stem = strip_date_prefix(item)
        if stem in overrides:
            dest_path = resolve_destination(overrides[stem], plans_dir)
            if dest_path is None:
                print("destination does not exist for override %s: %s" % (item, overrides[stem]), file=sys.stderr)
                return 2
            mappings.append((item, dest_path))
            continue
        dest, _tied = match_item(item, plan_names)
        if dest is None:
            mappings.append((item, args.self_host))
        else:
            mappings.append((item, os.path.join(plans_dir, dest)))

    item_rel = lambda name: rel(os.path.join(inbox, name), reg.root)

    for item, dest_path in mappings:
        name = os.path.basename(item)
        former_rel = item_rel(name)
        self_hosted = os.path.abspath(dest_path) == os.path.abspath(args.self_host)
        dest_rel = rel(dest_path, reg.root)

        # License: item row (existing or appended) with a user-approved note.
        row = reg.row_for_src_suffix(name)
        if row is None:
            identity = reg.next_identity(strip_date_prefix(name), item_date(name))
            note = ("user-approved %s: migration audit - disposition folded into %s; per-item file deleted"
                    % (date, dest_rel))
            reg.append_row(identity, former_rel, date, note)
        else:
            idx, cells = row
            if cells[8].strip():
                note = cells[8] + ("; migrated %s: disposition folded into %s; per-item file deleted"
                                   % (date, dest_rel))
            else:
                note = ("user-approved %s: migration audit - disposition folded into %s; per-item file deleted"
                        % (date, dest_rel))
            reg.set_audit(idx, cells, note)

        if not self_hosted:
            # License: destination row note (backfill the row when missing).
            drow = reg.row_for_src_suffix(os.path.basename(dest_path))
            if drow is None:
                dcells_base = strip_date_prefix(os.path.basename(dest_path))
                identity = reg.next_identity(dcells_base, item_date(os.path.basename(dest_path)))
                note = ("user-approved %s: migration audit - received %s disposition (per-item file deleted)"
                        % (date, former_rel))
                reg.append_row(identity, dest_rel, date, note)
            else:
                idx, cells = drow
                if cells[8].strip():
                    note = cells[8] + ("; received %s disposition (per-item file deleted)" % former_rel)
                else:
                    note = ("user-approved %s: migration audit - received %s disposition (per-item file deleted)"
                            % (date, former_rel))
                reg.set_audit(idx, cells, note)

        bullet = "- %s: disposition folded into %s (%s); per-item file deleted.\n" % (
            former_rel, os.path.basename(args.self_host) if self_hosted else os.path.basename(dest_path), date)
        append_bullet(dest_path, bullet)
        os.remove(os.path.join(inbox, name))

    write_lines(reg.path, reg.lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
