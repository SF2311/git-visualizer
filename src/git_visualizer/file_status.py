"""Working Tree and Staging Area entries from ``git status --porcelain=v2 -z``.

The command itself is run by :mod:`git_visualizer.git_reader` with optional locks
disabled, so reading status never takes the index lock or rewrites the index (ADR 0001).
"""

from __future__ import annotations

from git_visualizer.snapshot import ChangeKind, FileEntry

STATUS_ARGS = (
    "status",
    "--porcelain=v2",
    "-z",
    "--untracked-files=all",
    "--renames",
    "--ignore-submodules=none",
)

_INDEX_CHANGES = {
    "A": ChangeKind.NEW,
    "C": ChangeKind.NEW,
    "M": ChangeKind.MODIFIED,
    "T": ChangeKind.MODIFIED,
    "D": ChangeKind.DELETED,
    "R": ChangeKind.RENAMED,
}
_WORKING_TREE_CHANGES = {
    "A": ChangeKind.NEW,  # intent-to-add (`git add -N`)
    "M": ChangeKind.MODIFIED,
    "T": ChangeKind.MODIFIED,
    "D": ChangeKind.DELETED,
}


def parse_status(output: str) -> tuple[tuple[FileEntry, ...], tuple[FileEntry, ...]]:
    """Parse porcelain v2 (``-z``) output into (Working Tree, Staging Area) entries.

    Unchanged files never appear in git's output, so they are never listed. A file
    with both staged and unstaged changes yields one entry in each column.
    """
    working_tree: list[FileEntry] = []
    staging_area: list[FileEntry] = []
    fields = output.split("\0")
    position = 0
    while position < len(fields):
        record = fields[position]
        position += 1
        if not record:
            continue
        kind = record[0]
        if kind == "?":
            working_tree.append(FileEntry(record[2:], ChangeKind.UNTRACKED))
        elif kind == "1":
            xy, path = _split(record, 8)
            _add_ordinary(xy, path, None, working_tree, staging_area)
        elif kind == "2":
            xy, path = _split(record, 9)
            original_path = fields[position]
            position += 1
            _add_ordinary(xy, path, original_path, working_tree, staging_area)
        elif kind == "u":
            xy, path = _split(record, 10)
            working_tree.append(FileEntry(path, _conflict_change(xy), conflicted=True))
        # "#" headers and "!" ignored files are not shown.
    return tuple(sorted(working_tree, key=_by_path)), tuple(sorted(staging_area, key=_by_path))


def _split(record: str, path_field: int) -> tuple[str, str]:
    """XY status and path of a record whose path is field number ``path_field``."""
    parts = record.split(" ", path_field)
    return parts[1], parts[path_field]


def _add_ordinary(
    xy: str,
    path: str,
    original_path: str | None,
    working_tree: list[FileEntry],
    staging_area: list[FileEntry],
) -> None:
    index_status, working_tree_status = xy[0], xy[1]
    if index_status in _INDEX_CHANGES:
        change = _INDEX_CHANGES[index_status]
        renamed_from = original_path if change is ChangeKind.RENAMED else None
        staging_area.append(FileEntry(path, change, original_path=renamed_from))
    if working_tree_status in _WORKING_TREE_CHANGES:
        working_tree.append(FileEntry(path, _WORKING_TREE_CHANGES[working_tree_status]))


def _conflict_change(xy: str) -> ChangeKind:
    if "D" in xy:
        return ChangeKind.DELETED
    if xy == "AA":
        return ChangeKind.NEW
    return ChangeKind.MODIFIED


def _by_path(entry: FileEntry) -> str:
    return entry.path
