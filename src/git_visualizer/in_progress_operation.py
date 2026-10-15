"""Detect the In-progress Operation from git's own state files in the git directory.

Git records a paused merge, rebase, cherry-pick or revert by files such as
``MERGE_HEAD`` or ``rebase-merge/``. They are only read here, never written or
removed (ADR 0001), and no git command is needed beyond locating the git directory.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from git_visualizer.snapshot import FileEntry, InProgressOperation, OperationKind

# Checked after the rebase directories: a rebase replays commits by picking them, so it
# is the rebase, not a cherry-pick, that the lecturer is in.
_HEAD_FILES = (
    ("MERGE_HEAD", OperationKind.MERGE),
    ("CHERRY_PICK_HEAD", OperationKind.CHERRY_PICK),
    ("REVERT_HEAD", OperationKind.REVERT),
)


def read_in_progress_operation(
    git_dir: Path, working_tree: Sequence[FileEntry]
) -> InProgressOperation | None:
    """The In-progress Operation recorded in ``git_dir``, or ``None``.

    The conflict count is taken from the conflicted ``working_tree`` entries, i.e. the
    files git still lists as unmerged.
    """
    conflict_count = len({entry.path for entry in working_tree if entry.conflicted})
    rebase = _rebase_progress(git_dir)
    if rebase is not None:
        step, total = rebase
        return InProgressOperation(OperationKind.REBASE, conflict_count, step, total)
    for name, kind in _HEAD_FILES:
        if (git_dir / name).is_file():
            return InProgressOperation(kind, conflict_count)
    return None


def _rebase_progress(git_dir: Path) -> tuple[int, int] | None:
    """(step, total) of a rebase in progress, or ``None`` when there is none.

    ``rebase-merge/`` (the default and interactive backend) records ``msgnum``/``end``;
    ``rebase-apply/`` (the apply backend) records ``next``/``last``, but is also used
    by ``git am``, which marks itself with an ``applying`` file.
    """
    merge_backend = git_dir / "rebase-merge"
    if merge_backend.is_dir():
        return _number(merge_backend / "msgnum"), _number(merge_backend / "end")
    apply_backend = git_dir / "rebase-apply"
    if apply_backend.is_dir() and not (apply_backend / "applying").exists():
        return _number(apply_backend / "next"), _number(apply_backend / "last")
    return None


def _number(file: Path) -> int:
    """The integer stored in ``file``; 0 if it is missing or unreadable (e.g. mid-write)."""
    try:
        return int(file.read_text().strip())
    except (OSError, ValueError):
        return 0
