"""Watcher: calls "repository changed" whenever the Observed Repository changes on disk.

A thin adapter around :class:`QFileSystemWatcher`:

* watches the git directory (without ``objects/``) and the Working Tree (without
  ignored paths), or — while the folder is not a repository yet — the folder itself,
  so that ``git init`` is noticed;
* coalesces bursts of events: the callback runs once, ``debounce_ms`` after the last
  event of a burst (but at the latest ``max_delay_ms`` after its first event);
* polls a cheap fingerprint (directory listings with mtimes and sizes) every
  ``poll_interval_ms`` as a fallback against missed events (e.g. in-place appends to
  files that are not watched individually).

Passive (ADR 0001): it only stats files and runs read-only git commands.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QFileSystemWatcher, QObject, QTimer

from git_visualizer.git_reader import _Git

# Individually watched Working Tree files (directories are always watched); every
# watch costs a file descriptor on macOS, and polling covers the rest.
MAX_WATCHED_FILES = 1000

_Fingerprint = frozenset[tuple[str, int, int]]


@dataclass(frozen=True)
class _Targets:
    directories: frozenset[str]
    files: frozenset[str]
    ignored: frozenset[str]


class RepositoryWatcher(QObject):
    def __init__(
        self,
        folder: Path | str,
        on_repository_changed: Callable[[], object],
        *,
        debounce_ms: int = 150,
        max_delay_ms: int = 1000,
        poll_interval_ms: int = 2000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._folder = Path(folder)
        self._on_repository_changed = on_repository_changed
        self._max_delay_ms = max_delay_ms

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_event)
        self._watcher.directoryChanged.connect(self._on_event)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(debounce_ms)
        self._debounce.timeout.connect(self._fire)
        self._pending_since = QElapsedTimer()

        self._poll = QTimer(self)
        self._poll.setInterval(poll_interval_ms)
        self._poll.timeout.connect(self._check_fingerprint)

        self._targets = _find_targets(self._folder)
        self._fingerprint = _fingerprint(self._targets)
        self._watch(self._targets)
        self._poll.start()

    def stop(self) -> None:
        self._poll.stop()
        self._debounce.stop()
        self._watch(_Targets(frozenset(), frozenset(), frozenset()))

    def _on_event(self, _path: str) -> None:
        if not self._debounce.isActive():
            self._pending_since.start()
            self._debounce.start()
        elif self._pending_since.elapsed() < self._max_delay_ms:
            self._debounce.start()  # restart: wait for the burst to settle

    def _check_fingerprint(self) -> None:
        if not self._debounce.isActive() and _fingerprint(self._targets) != self._fingerprint:
            self._on_event("")

    def _fire(self) -> None:
        # Fingerprint *before* reading, so a change during the read is caught by polling.
        targets = _find_targets(self._folder)
        fingerprint = _fingerprint(targets)
        self._on_repository_changed()
        self._targets, self._fingerprint = targets, fingerprint
        self._watch(targets)

    def _watch(self, targets: _Targets) -> None:
        wanted = targets.directories | targets.files
        watched = set(self._watcher.directories()) | set(self._watcher.files())
        if obsolete := sorted(watched - wanted):
            self._watcher.removePaths(obsolete)
        if new := sorted(wanted - watched):
            existing = [path for path in new if os.path.exists(path)]
            if existing:
                self._watcher.addPaths(existing)


def _find_targets(folder: Path) -> _Targets:
    git = _Git(folder)
    top_level = git.run_optional("rev-parse", "--show-toplevel")
    git_dir = git.run_optional("rev-parse", "--absolute-git-dir")
    common_dir = git.run_optional("rev-parse", "--path-format=absolute", "--git-common-dir")
    if git_dir is None:
        return _Targets(frozenset({str(folder)}), frozenset(), frozenset())

    directories: set[str] = {str(folder)}
    for directory in {git_dir.strip(), (common_dir or git_dir).strip()}:
        directories.update(_walk_directories(Path(directory), skip=lambda p: p.name == "objects"))

    files: set[str] = set()
    ignored: frozenset[str] = frozenset()
    if top_level is not None:
        root = Path(top_level.strip())
        ignored = _ignored_paths(root)
        work_tree_dirs = _walk_directories(
            root, skip=lambda p: p.name == ".git" or str(p) in ignored
        )
        directories.update(work_tree_dirs)
        files = _files_in(work_tree_dirs, ignored)
    return _Targets(frozenset(directories), frozenset(files), ignored)


def _ignored_paths(root: Path) -> frozenset[str]:
    output = _Git(root).run_optional(
        "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory"
    )
    if not output:
        return frozenset()
    return frozenset(str(root / entry.rstrip("/")) for entry in output.split("\0") if entry)


def _walk_directories(root: Path, *, skip: Callable[[Path], bool]) -> list[str]:
    directories = []
    for current, subdirectories, _files in os.walk(root):
        directories.append(current)
        subdirectories[:] = sorted(d for d in subdirectories if not skip(Path(current, d)))
    return directories


def _files_in(directories: Iterable[str], ignored: frozenset[str]) -> set[str]:
    files: set[str] = set()
    for directory in directories:
        for entry in _scan(directory):
            if len(files) >= MAX_WATCHED_FILES:
                return files
            if entry.is_file(follow_symlinks=False) and entry.path not in ignored:
                files.add(entry.path)
    return files


def _fingerprint(targets: _Targets) -> _Fingerprint:
    """Every watched directory and its direct entries, with mtime and size."""
    stamps = []
    for directory in targets.directories:
        for path in [directory, *(entry.path for entry in _scan(directory))]:
            if path in targets.ignored:
                continue
            try:
                stat = os.stat(path, follow_symlinks=False)
            except OSError:
                continue
            stamps.append((path, stat.st_mtime_ns, stat.st_size))
    return frozenset(stamps)


def _scan(directory: str) -> list[os.DirEntry[str]]:
    try:
        with os.scandir(directory) as entries:
            return list(entries)
    except OSError:
        return []
