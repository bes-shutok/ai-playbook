#!/bin/bash
set -euo pipefail

docs_branch_sync_main() {
python3 - "$@" <<'PY'
from __future__ import annotations

import calendar
import fcntl
import ntpath
import os
import posixpath
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import tomllib


class SyncError(Exception):
    pass


@dataclass(frozen=True)
class ArchiveRoot:
    role: str
    relative: str
    absolute: Path


@dataclass(frozen=True)
class LocalFile:
    mode: str
    data: bytes
    mtime: float


@dataclass(frozen=True)
class BranchFile:
    mode: str
    oid: str
    path: str


GIT_ROUTING_VARS = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_NAMESPACE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
}


def git_environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    for key in GIT_ROUTING_VARS:
        merged.pop(key, None)
    merged["GIT_OPTIONAL_LOCKS"] = "0"
    if overrides:
        merged.update(overrides)
    return merged


def git(args: list[str], *, cwd: Path, env: dict[str, str] | None = None, check: bool = True, input_data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    merged = git_environment(env)
    result = subprocess.run(["git", *args], cwd=cwd, env=merged, input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise SyncError(f"git {' '.join(args)} failed: {detail or result.returncode}")
    return result


def fail(message: str) -> None:
    raise SyncError(message)


def docs_sync_lock(repo: Path):
    common = Path(os.fsdecode(git(["rev-parse", "--git-common-dir"], cwd=repo).stdout.strip()))
    if not common.is_absolute():
        common = (repo / common).resolve()
    common.mkdir(parents=True, exist_ok=True)
    stream = open(common / "docs-branch-sync.lock", "a", encoding="utf-8")
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
    return stream


def trace(stage: str) -> None:
    target = os.environ.get("DOCS_SYNC_TRACE_FILE")
    if target:
        with open(target, "a", encoding="utf-8") as stream:
            stream.write(stage + "\n")


# The runner-owned merge-lock span (plan 2026-10-10-done-closeout-lock-span
# Task 1): the mutating runners acquire and release the repository-keyed merge
# lock inside this process, so the hold is the runner's own runtime with no
# agent-turn gaps and no lock exports ever entering chat context. The done
# lock script resolves two-tier: the DONE_LOCK_SCRIPT override, the synced
# repository's own scripts/ copy, then the deployed runtime-home copy.
MERGE_ACQUIRE_BASE = "merge-wait-acquire --label docs-branch-sync"
MERGE_LOCK_WAIT_DEFAULT_SECS = 300


def merge_lock_max_wait() -> int:
    raw = os.environ.get("DOCS_SYNC_MERGE_MAX_WAIT", "").strip()
    if not raw:
        return MERGE_LOCK_WAIT_DEFAULT_SECS
    try:
        wait = int(raw)
    except ValueError:
        fail(f"DOCS_SYNC_MERGE_MAX_WAIT must be an integer seconds count: {raw!r}")
    if wait < 0:
        fail(f"DOCS_SYNC_MERGE_MAX_WAIT must not be negative: {raw!r}")
    return wait


def done_lock_script(repo: Path) -> Path:
    override = os.environ.get("DONE_LOCK_SCRIPT")
    if override:
        return Path(override)
    local = repo / "scripts" / "done-lock.sh"
    if local.is_file():
        return local
    return Path.home() / ".ai-playbook" / "scripts" / "done-lock.sh"


def parse_merge_lock_exports(text: str) -> dict[str, str]:
    exports: dict[str, str] = {}
    for line in text.splitlines():
        for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
            prefix = f"export {name}="
            if line.startswith(prefix):
                raw = line[len(prefix):]
                try:
                    exports[name] = shlex.split(raw)[0]
                except (ValueError, IndexError):
                    exports[name] = raw
    return exports


class MergeLockSpan:
    """One runner-owned merge-lock hold: a bounded-wait acquire whose exports
    are parsed in-process (never exported into this process's environment or
    printed), and an always-run release that prints exactly one held-span
    stderr line. A release failure is loud on stderr and never masks the
    mutation's own outcome; the operator escapes stay merge-status and
    merge-stale-clean."""

    def __init__(self, repo: Path):
        self.repo = repo
        self.exports: dict[str, str] = {}
        self.started: float | None = None

    def acquire(self) -> None:
        script = done_lock_script(self.repo)
        command = [
            "bash", str(script), *MERGE_ACQUIRE_BASE.split(),
            "--max-wait", str(merge_lock_max_wait()),
        ]
        try:
            result = subprocess.run(
                command, cwd=self.repo, env=git_environment(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except OSError as exc:
            fail(f"merge lock acquire failed: the lock script could not be launched: {exc}")
        if result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip()
            fail(f"merge lock acquire refused after the bounded wait; the docs ref stays unchanged. holder evidence: {detail}")
        exports = parse_merge_lock_exports(result.stdout.decode("utf-8", "replace"))
        if "MERGE_LOCK_DIR" not in exports or "MERGE_LOCK_TOKEN" not in exports:
            fail("merge lock acquire produced no MERGE_LOCK exports to release against")
        self.exports = exports
        self.started = time.monotonic()
        trace("merge-acquire")

    def release(self) -> None:
        if not self.exports:
            return
        exports, self.exports = self.exports, {}
        held = 0.0 if self.started is None else time.monotonic() - self.started
        env = git_environment()
        env.update(exports)
        try:
            result = subprocess.run(
                ["bash", str(done_lock_script(self.repo)), "merge-release"],
                cwd=self.repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except OSError as exc:
            print(f"merge-lock: held {held:.1f}s", file=sys.stderr)
            print(f"ERROR: docs-branch sync merge-lock release failed: {exc}", file=sys.stderr)
            return
        print(f"merge-lock: held {held:.1f}s", file=sys.stderr)
        if result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip()
            print(
                f"ERROR: docs-branch sync merge-lock release failed (exit {result.returncode}); "
                f"run merge-status and report the holder state: {detail}",
                file=sys.stderr,
            )


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def parse_facts(repo: Path) -> dict[str, object]:
    facts_path = repo / ".ai-playbook" / "facts.md"
    if not facts_path.is_file():
        fail("cannot read .ai-playbook/facts.md; refusing before archive traversal")
    try:
        content = facts_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"cannot read .ai-playbook/facts.md: {exc}")
    match = re.search(r"(?ms)^```toml[ \t]*\r?\n(.*?)^```[ \t]*$", content)
    if not match:
        fail(".ai-playbook/facts.md has no TOML facts block")
    try:
        facts = tomllib.loads(match.group(1))
    except tomllib.TOMLDecodeError as exc:
        fail(f".ai-playbook/facts.md TOML is malformed: {exc}")
    if not isinstance(facts, dict):
        fail(".ai-playbook/facts.md TOML must be a table")
    return facts


def normalize_root(value: object, role: str, *, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be a non-empty relative docs path")
    raw = value.strip().replace("\\", "/")
    if not raw:
        fail(f"{label} is empty")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        fail(f"{label} must be relative: {value!r}")
    parts = raw.split("/")
    if any(part in (".", "..") for part in parts):
        fail(f"{label} contains a dot or parent component: {value!r}")
    parts = [part for part in parts if part]
    if len(parts) < 2 or parts[0] not in ("docs", ".ai-playbook"):
        fail(f"{label} must be a narrow root below docs/ or the audit home .ai-playbook/: {value!r}")
    if parts[-1] != role:
        fail(f"{label} must end in the {role!r} archive role: {value!r}")
    return "/".join(parts)


def resolve_roots(repo: Path, facts: dict[str, object]) -> list[ArchiveRoot]:
    docs = (repo / "docs").resolve(strict=False)
    audit_home = (repo / ".ai-playbook").resolve(strict=False)
    if not is_within(docs, repo):
        fail("docs/ resolves outside the repository")
    # Retention contract (single home; plan
    # 2026-10-11-review-certs-seal-home-untracked Task 3): the docs branch
    # retains review records, metrics, and seals; seals are untracked run
    # artifacts on main and are never committed going forward; the sync must
    # run from the checkout holding the seal corpus.
    specs = [
        ("reviews", "docs/reviews", "fixed docs/reviews"),
        ("reviews", facts.get("reviews_dir", ".ai-playbook/reviews"), "reviews_dir"),
        ("metrics", facts.get("metrics_dir", ".ai-playbook/metrics"), "metrics_dir"),
        ("review-certs", facts.get("review_certs_dir", ".ai-playbook/review-certs"), "review_certs_dir"),
    ]
    resolved: list[ArchiveRoot] = []
    for role, value, label in specs:
        relative = normalize_root(value, role, label=label)
        absolute = (repo / relative).resolve(strict=False)
        if not (is_within(absolute, docs) or is_within(absolute, audit_home)) or not is_within(absolute, repo):
            fail(f"{label} resolves outside docs/ and the audit home: {relative}")
        if absolute.name != role:
            fail(f"{label} resolves to the wrong archive role: {absolute.relative_to(repo).as_posix()}")
        canonical = absolute.relative_to(repo).as_posix()
        resolved.append(ArchiveRoot(role, canonical, absolute))

    for index, left in enumerate(resolved):
        for right in resolved[index + 1:]:
            if left.role == right.role:
                continue
            if is_within(left.absolute, right.absolute) or is_within(right.absolute, left.absolute):
                fail(f"archive roots overlap across roles: {left.relative} and {right.relative}")

    merged: list[ArchiveRoot] = []
    for root in sorted(resolved, key=lambda item: (item.role, len(item.relative), item.relative)):
        same_role = [item for item in merged if item.role == root.role]
        if any(is_within(root.absolute, item.absolute) for item in same_role):
            continue
        merged = [item for item in merged if not (item.role == root.role and is_within(item.absolute, root.absolute))]
        merged.append(root)
    return sorted(merged, key=lambda item: item.relative)


def cutoff_from_now(raw: str | None) -> datetime:
    if raw:
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            fail(f"DOCS_SYNC_NOW must be an ISO timestamp: {exc}")
        if value.tzinfo is None:
            fail("DOCS_SYNC_NOW must include a timezone")
        now = value.astimezone(timezone.utc)
    else:
        now = datetime.now(timezone.utc)
    month_index = now.year * 12 + now.month - 1 - 2
    target_year, zero_month = divmod(month_index, 12)
    target_month = zero_month + 1
    target_day = min(now.day, calendar.monthrange(target_year, target_month)[1])
    return now.replace(year=target_year, month=target_month, day=target_day)


def path_is_under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def root_for(path: str, roots: list[ArchiveRoot]) -> ArchiveRoot | None:
    parts = path.split("/")
    matches = [
        root for root in roots
        if len(parts) > len(root.relative.split("/"))
        and parts[:len(root.relative.split("/"))] == root.relative.split("/")
    ]
    return max(matches, key=lambda item: len(item.relative)) if matches else None


def validate_branch_paths(branch: dict[str, BranchFile]) -> None:
    for path in branch:
        parts = path.split("/")
        if (
            not path
            or path.startswith("/")
            or "\\" in path
            or ntpath.splitdrive(path)[0]
            or any(part in ("", ".", "..") for part in parts)
        ):
            fail(f"invalid docs-branch tree path; refusing before restore: {path!r}")


def symlink_target_is_under(path: str, target: str, root: str, links: dict[str, str] | None = None) -> bool:
    links = links or {}
    if target.startswith("/") or ntpath.isabs(target) or ntpath.splitdrive(target)[0]:
        return False
    components = posixpath.dirname(path).split("/")
    pending = target.replace("\\", "/").split("/")
    expansions = 0
    while pending:
        component = pending.pop(0)
        if component in ("", "."):
            continue
        if component == "..":
            if components:
                components.pop()
            resolved = "/".join(components)
            if not path_is_under(resolved, root):
                return False
            continue
        components.append(component)
        prefix = "/".join(components)
        link_target = links.get(prefix)
        if link_target is None:
            if not path_is_under(prefix, root):
                return False
            continue
        if link_target.startswith("/") or ntpath.isabs(link_target) or ntpath.splitdrive(link_target)[0]:
            return False
        expansions += 1
        if expansions > len(links) + 1:
            return False
        components.pop()
        pending = link_target.replace("\\", "/").split("/") + pending
    resolved = "/".join(components)
    return path_is_under(resolved, root)


def collect_local_files(repo: Path, roots: list[ArchiveRoot]) -> dict[str, LocalFile]:
    discovered: list[tuple[ArchiveRoot, Path, os.stat_result, str | None]] = []
    trace("candidate-walk")
    for root in roots:
        descriptors: list[int] = []
        try:
            try:
                root_fd, descriptors = open_repo_directory(repo, Path(root.relative).parts, create=False)
            except FileNotFoundError:
                continue

            def walk(directory_fd: int, relative_parts: tuple[str, ...]) -> None:
                for entry in sorted(os.scandir(directory_fd), key=lambda item: item.name):
                    name = entry.name
                    info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    candidate_parts = (*relative_parts, name)
                    candidate = repo.joinpath(*candidate_parts)
                    if stat.S_ISLNK(info.st_mode):
                        target = os.readlink(name, dir_fd=directory_fd)
                        discovered.append((root, candidate, info, target))
                    elif stat.S_ISDIR(info.st_mode):
                        child_fd = os.open(
                            name, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                            dir_fd=directory_fd,
                        )
                        try:
                            actual = os.fstat(child_fd)
                            if (actual.st_dev, actual.st_ino) != (info.st_dev, info.st_ino):
                                raise OSError(f"archive directory changed after validation: {candidate}")
                            walk(child_fd, candidate_parts)
                        finally:
                            os.close(child_fd)
                    else:
                        discovered.append((root, candidate, info, None))

            walk(root_fd, Path(root.relative).parts)
        except OSError as exc:
            fail(f"cannot safely traverse archive root {root.relative}: {exc}")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    links = {candidate.relative_to(repo).as_posix(): target for _, candidate, info, target in discovered if target is not None}
    for root, candidate, info, target in discovered:
        if target is not None and not symlink_target_is_under(
            candidate.relative_to(repo).as_posix(), target, root.relative, links
        ):
            fail(f"archive symlink escapes its allowed root: {candidate.relative_to(repo).as_posix()} -> {target}")

    files: dict[str, LocalFile] = {}
    for root, candidate, info, target in discovered:
        relative = candidate.relative_to(repo).as_posix()
        if stat.S_ISLNK(info.st_mode):
            files[relative] = LocalFile("120000", os.fsencode(target or ""), info.st_mtime)
        elif stat.S_ISREG(info.st_mode):
            try:
                data = read_regular_candidate(repo, root, candidate, info)
            except OSError as exc:
                fail(f"cannot read archive file {relative}: {exc}")
            mode = "100755" if info.st_mode & 0o111 else "100644"
            files[relative] = LocalFile(mode, data, info.st_mtime)
    trace("snapshot")
    return files


def read_regular_candidate(repo: Path, root: ArchiveRoot, candidate: Path, expected: os.stat_result) -> bytes:
    """Read the validated inode through no-follow directory descriptors."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    descriptors: list[int] = []
    try:
        relative_parts = candidate.relative_to(root.absolute).parts
        directory_fd, descriptors = open_repo_directory(
            repo, (*Path(root.relative).parts, *relative_parts[:-1]), create=False
        )
        file_fd = os.open(relative_parts[-1], os.O_RDONLY | nofollow, dir_fd=directory_fd)
        descriptors.append(file_fd)
        actual = os.fstat(file_fd)
        if not stat.S_ISREG(actual.st_mode) or (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
            raise OSError(f"archive file changed after validation: {candidate}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def open_repo_directory(repo: Path, parts: tuple[str, ...], *, create: bool) -> tuple[int, list[int]]:
    """Open a repository-relative directory chain without following symlinks."""
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptors = [os.open(repo, directory_flags)]
    current = descriptors[0]
    try:
        for part in parts:
            try:
                child = os.open(part, directory_flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, mode=0o755, dir_fd=current)
                child = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(child)
            current = child
        return current, descriptors
    except OSError:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise


def read_branch_tree(repo: Path, old_tip: str | None) -> dict[str, BranchFile]:
    if old_tip is None:
        return {}
    raw = git(["ls-tree", "-r", "-z", "--full-tree", old_tip], cwd=repo).stdout
    files: dict[str, BranchFile] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, object_type, oid = metadata.decode("ascii").split(" ", 2)
        if object_type != "blob" and mode != "160000":
            continue
        path = os.fsdecode(path_bytes)
        files[path] = BranchFile(mode, oid, path)
    return files


def branch_blobs(repo: Path, entries: list[BranchFile]) -> dict[str, bytes]:
    object_ids = sorted({entry.oid for entry in entries})
    if not object_ids:
        return {}
    raw = git(
        ["cat-file", "--batch"], cwd=repo,
        input_data=("\n".join(object_ids) + "\n").encode("ascii"),
    ).stdout
    blobs: dict[str, bytes] = {}
    offset = 0
    for requested in object_ids:
        header_end = raw.find(b"\n", offset)
        if header_end < 0:
            fail("git cat-file --batch returned an incomplete header")
        header = raw[offset:header_end].decode("ascii", "replace").split()
        if len(header) != 3 or header[0] != requested or header[1] != "blob":
            fail(f"git cat-file --batch returned an invalid blob header for {requested}")
        try:
            size = int(header[2])
        except ValueError:
            fail(f"git cat-file --batch returned an invalid blob size for {requested}")
        data_start = header_end + 1
        data_end = data_start + size
        if data_end >= len(raw) or raw[data_end:data_end + 1] != b"\n":
            fail(f"git cat-file --batch returned truncated blob data for {requested}")
        blobs[requested] = raw[data_start:data_end]
        offset = data_end + 1
    if offset != len(raw):
        fail("git cat-file --batch returned unexpected trailing data")
    return blobs


def branch_path_times(repo: Path, paths: set[str]) -> dict[str, float]:
    if not paths:
        return {}
    raw = git(["log", "--format=%ct%x00", "--name-only", "-z", "refs/heads/docs"], cwd=repo).stdout
    wanted = set(paths)
    found: dict[str, float] = {}
    current_time: float | None = None
    for record in raw.split(b"\0"):
        if not record:
            continue
        if record.isdigit():
            current_time = float(record)
            continue
        if record.startswith(b"\n"):
            record = record[1:]
        path = os.fsdecode(record)
        if current_time is not None and path in wanted and path not in found:
            found[path] = current_time
            if len(found) == len(wanted):
                break
    missing = sorted(wanted - found.keys())
    if missing:
        fail(f"cannot find docs-branch change timestamps for {', '.join(missing[:3])}")
    return found


def build_archive(repo: Path, roots: list[ArchiveRoot], local: dict[str, LocalFile], branch: dict[str, BranchFile], cutoff: datetime) -> tuple[dict[str, tuple[str, bytes]], list[str], list[str]]:
    cutoff_epoch = cutoff.timestamp()
    kept: dict[str, tuple[str, bytes]] = {}
    restore: list[str] = []
    removed: list[str] = []
    local_paths = set(local)
    branch_allowed = {path: entry for path, entry in branch.items() if root_for(path, roots) is not None}
    branch_data = branch_blobs(repo, [entry for entry in branch_allowed.values() if entry.mode != "160000"])

    branch_links = {
        path: os.fsdecode(branch_data[entry.oid])
        for path, entry in branch_allowed.items()
        if entry.mode == "120000"
    }
    path_times = branch_path_times(repo, set(branch_allowed))
    for path, entry in branch_allowed.items():
        root = root_for(path, roots)
        if root is None:
            continue
        if entry.mode == "160000":
            removed.append(path)
            continue
        old_data = branch_data[entry.oid]
        if entry.mode == "120000":
            target = os.fsdecode(old_data)
            if not symlink_target_is_under(path, target, root.relative, branch_links):
                fail(f"docs-branch archive symlink escapes its allowed root: {path} -> {target}")
        changed_at = path_times[path]
        recent_branch = changed_at >= cutoff_epoch
        source = local.get(path)
        if source is None:
            if recent_branch:
                kept[path] = (entry.mode, old_data)
                restore.append(path)
            else:
                removed.append(path)
            continue
        same_bytes = source.data == old_data
        if recent_branch:
            kept[path] = (source.mode, source.data) if not same_bytes and source.mtime >= cutoff_epoch else (entry.mode, old_data)
        elif source.mtime >= cutoff_epoch and not same_bytes:
            kept[path] = (source.mode, source.data)
        else:
            removed.append(path)

    for path, source in local.items():
        if path in branch_allowed:
            continue
        if source.mtime >= cutoff_epoch:
            kept[path] = (source.mode, source.data)

    allowed_old_paths = set(branch_allowed)
    for path in branch:
        if path not in allowed_old_paths:
            removed.append(path)

    trace("prune")
    removed = sorted(set(removed) - set(kept))
    restore = sorted(path for path in set(restore) if path in kept and path not in local_paths)
    return kept, restore, removed


def index_tree(repo: Path, paths: dict[str, tuple[str, bytes]], index_path: Path) -> str:
    env = {"GIT_INDEX_FILE": str(index_path)}
    git(["read-tree", "--empty"], cwd=repo, env=env)
    if paths:
        with tempfile.TemporaryDirectory(prefix="docs-branch-blobs-") as temporary:
            root = Path(temporary)
            ordered = sorted(paths.items())
            blob_paths = []
            for index, (_, (_, data)) in enumerate(ordered):
                blob_path = root / str(index)
                blob_path.write_bytes(data)
                blob_paths.append(blob_path)
            hashed = git(["hash-object", "-w", "--stdin-paths"], cwd=repo, input_data=("\n".join(map(str, blob_paths)) + "\n").encode()).stdout.decode("ascii").splitlines()
        if len(hashed) != len(ordered):
            fail("git returned an incomplete batch of archive object IDs")
        index_info = b"".join(
            f"{mode} {oid}\t{path}".encode("utf-8", "surrogateescape") + b"\0"
            for (path, (mode, _)), oid in zip(ordered, hashed)
        )
        git(["update-index", "-z", "--index-info"], cwd=repo, env=env, input_data=index_info)
    return git(["write-tree"], cwd=repo, env=env).stdout.decode("ascii").strip()


def create_commit(repo: Path, tree: str, old_tip: str | None) -> str:
    args = ["commit-tree", tree]
    if old_tip:
        args.extend(["-p", old_tip])
    args.extend(["-m", "docs: retain recent analysis archives"])
    return git(args, cwd=repo).stdout.decode("ascii").strip()


def staged_deletions(repo: Path) -> set[str]:
    raw = git(["diff", "--cached", "--name-only", "--no-renames", "--diff-filter=D", "-z"], cwd=repo).stdout
    return {os.fsdecode(path) for path in raw.split(b"\0") if path}


def restore_files(repo: Path, roots: list[ArchiveRoot], paths: list[str], entries: dict[str, tuple[str, bytes]]) -> None:
    staged = staged_deletions(repo)
    for relative in paths:
        validate_branch_paths({relative: BranchFile("", "", relative)})
        if root_for(relative, roots) is None:
            fail(f"refusing to restore path outside allowed archive roots: {relative}")
        if relative in staged:
            continue
        mode, data = entries[relative]
        parts = Path(relative).parts
        descriptors: list[int] = []
        try:
            parent_fd, descriptors = open_repo_directory(repo, parts[:-1], create=True)
            if mode == "120000":
                os.symlink(os.fsdecode(data), parts[-1], dir_fd=parent_fd)
            else:
                descriptor = os.open(
                    parts[-1], os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                    0o755 if mode == "100755" else 0o644, dir_fd=parent_fd
                )
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(data)
        except FileExistsError:
            continue
        except OSError as exc:
            fail(f"cannot restore recent docs-branch archive {relative}: {exc}")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)
        print(f"docs-branch: restored {relative} from refs/heads/docs")


def apply_tree(repo: Path, tree: str, old_tip: str | None) -> str | None:
    zero = "0" * len(git(["hash-object", "--stdin"], cwd=repo, input_data=b"").stdout.decode("ascii").strip())
    if old_tip:
        old_tree = git(["rev-parse", f"{old_tip}^{{tree}}"], cwd=repo).stdout.decode("ascii").strip()
        if old_tree == tree:
            update_docs_ref(repo, old_tip, old_tip)
            return old_tip
    elif not tree_has_entries(repo, tree):
        verify_docs_ref_absent(repo, expected=zero)
        return None

    expected = old_tip or zero
    new_commit = create_commit(repo, tree, old_tip)
    update_docs_ref(repo, new_commit, expected)
    return new_commit


def tree_has_entries(repo: Path, tree: str) -> bool:
    result = git(["ls-tree", "-r", "--name-only", tree], cwd=repo)
    return bool(result.stdout.strip())


def require_direct_docs_ref(repo: Path) -> None:
    symbolic = git(["symbolic-ref", "--quiet", "refs/heads/docs"], cwd=repo, check=False)
    if symbolic.returncode == 0:
        fail("refs/heads/docs must be a direct ref; symbolic docs refs are refused")


def verify_docs_ref_absent(repo: Path, *, expected: str) -> None:
    trace("ref-verify-absent")
    require_direct_docs_ref(repo)
    result = git(["update-ref", "--no-deref", "refs/heads/docs", expected, expected], cwd=repo, check=False)
    if result.returncode:
        fail("CAS refusal: refs/heads/docs was expected absent but a competing docs tip is current")


def update_docs_ref(repo: Path, new_tip: str, expected: str) -> None:
    trace("ref-update-cas")
    require_direct_docs_ref(repo)
    result = git(["update-ref", "--no-deref", "refs/heads/docs", new_tip, expected], cwd=repo, check=False)
    if result.returncode:
        fail("CAS refusal updating refs/heads/docs: a competing docs tip remains current; re-derive and retry")


def docs_ref_snapshot(repo: Path) -> str | None:
    result = git(
        ["for-each-ref", "--format=%(refname)%00%(symref)%00%(objectname)", "refs/heads/docs"],
        cwd=repo,
    )
    rows = result.stdout.decode("ascii").splitlines()
    direct_tip: str | None = None
    for row in rows:
        fields = row.split("\0")
        if len(fields) != 3:
            fail("Git returned an invalid docs-ref snapshot")
        refname, symbolic_target, object_name = fields
        if refname != "refs/heads/docs":
            fail("found invalid docs/* branches; consolidate them into refs/heads/docs first")
        if symbolic_target:
            fail("refs/heads/docs must be a direct ref; symbolic docs refs are refused")
        direct_tip = object_name
    return direct_tip


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    repo_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=Path.cwd(), env=git_environment(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if repo_result.returncode:
        fail("docs-branch sync must run inside a Git repository")
    repo = Path(os.fsdecode(repo_result.stdout.strip())).resolve()
    lock = docs_sync_lock(repo)
    try:
        if args:
            if len(args) != 2 or args[0] != "--append-witness":
                fail("usage: docs_branch_sync.sh [--append-witness WITNESS]")
            merge_lock = MergeLockSpan(repo)
            merge_lock.acquire()
            try:
                append_witness(repo, args[1])
            finally:
                merge_lock.release()
            return 0
        merge_lock = MergeLockSpan(repo)
        merge_lock.acquire()
        try:
            return sync(repo)
        finally:
            merge_lock.release()
    finally:
        lock.close()


def append_witness(repo: Path, witness: str) -> None:
    if not witness.startswith("lesson-scope-audit:"):
        fail("witness must start with lesson-scope-audit:")
    old_tip = docs_ref_snapshot(repo)
    if old_tip is None:
        fail("no docs branch; run a sync first")
    tree = git(["rev-parse", f"{old_tip}^{{tree}}"], cwd=repo).stdout.decode("ascii").strip()
    commit = git(
        ["-c", "user.name=docs-branch", "-c", "user.email=docs-branch@invalid", "commit-tree", tree,
         "-p", old_tip, "-m", "docs: lesson-scope-audit drift witness", "-m", witness], cwd=repo,
    ).stdout.decode("ascii").strip()
    try:
        update_docs_ref(repo, commit, old_tip)
    except SyncError:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        recovery = f"refs/docs-witness-recovery/{stamp}-{os.getpid()}"
        result = git(["update-ref", "--no-deref", recovery, commit], cwd=repo, check=False)
        if result.returncode:
            fail(f"CAS refused and recovery ref could not be created; witness commit {commit} remains in the object database")
        fail(f"docs tip changed; witness preserved at {recovery}; retry the docs sync, then rerun the witness append")


def sync(repo: Path) -> int:
    facts = parse_facts(repo)
    roots = resolve_roots(repo, facts)
    old_tip = docs_ref_snapshot(repo)

    local = collect_local_files(repo, roots)
    # collect_local_files validates every candidate symlink before reading file bytes.
    branch = read_branch_tree(repo, old_tip)
    validate_branch_paths(branch)
    cutoff = cutoff_from_now(os.environ.get("DOCS_SYNC_NOW"))
    archive, restore, removed = build_archive(repo, roots, local, branch, cutoff)

    for path in removed:
        print(f"docs-branch: pruned {path}")

    index_path: Path | None = None
    try:
        git_dir = Path(os.fsdecode(git(["rev-parse", "--absolute-git-dir"], cwd=repo).stdout.strip()))
        descriptor, raw_index = tempfile.mkstemp(prefix="docs-branch-index-", dir=git_dir)
        os.close(descriptor)
        index_path = Path(raw_index)
        tree = index_tree(repo, archive, index_path)
    finally:
        if index_path:
            index_path.unlink(missing_ok=True)

    new_tip = apply_tree(repo, tree, old_tip)
    if new_tip and new_tip != old_tip:
        print(f"docs-branch: landed {new_tip} on refs/heads/docs")
    elif old_tip:
        print(f"EMPTY-SYNC-SKIP: docs branch already matches the allowlisted archive tree at {old_tip}")
    else:
        print("EMPTY-SYNC-SKIP: no recent review or metrics archives; docs branch was not created")

    restore_files(repo, roots, restore, archive)
    print(f"docs-branch: sync complete ({len(archive)} archive files retained)")
    return 0


try:
    sys.exit(main())
except SyncError as exc:
    print(f"ERROR: docs-branch sync refused: {exc}", file=sys.stderr)
    sys.exit(1)
PY
}

docs_branch_sync_main "$@"
