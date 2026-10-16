"""Detect the In-progress Operation (merge, rebase, cherry-pick, revert) via the git CLI.

Merge, cherry-pick and revert are recognised by git resolving the pseudo-refs
``MERGE_HEAD``, ``CHERRY_PICK_HEAD`` and ``REVERT_HEAD`` (``git cat-file --batch-check``). A rebase and its progress
are the documented exception of ADR 0003: no git command prints the rebase step
counters for both backends, so the state directories are located with
``git rev-parse --git-path`` and only their counter files are read (never written).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from git_visualizer.git_cli import GitCli
from git_visualizer.snapshot import FileEntry, InProgressOperation, OperationKind

# Checked after the rebase directories: a rebase replays commits by picking them, so it
# is the rebase, not a cherry-pick, that the lecturer is in.
_OPERATION_HEADS = {
    "MERGE_HEAD": OperationKind.MERGE,
    "CHERRY_PICK_HEAD": OperationKind.CHERRY_PICK,
    "REVERT_HEAD": OperationKind.REVERT,
}


def read_in_progress_operation(git: GitCli, working_tree: Sequence[FileEntry]) -> InProgressOperation | None:
    """The In-progress Operation of the repository ``git`` runs in, or ``None``.

    The conflict count is taken from the conflicted ``working_tree`` entries, i.e. the
    files git still lists as unmerged.
    """
    conflict_count = len({entry.path for entry in working_tree if entry.conflicted})
    rebase = _rebase_progress(git)
    if rebase is not None:
        step, total = rebase
        return InProgressOperation(OperationKind.REBASE, conflict_count, step, total)
    # One line per name, in order: "<hash> <type> <size>", or "<name> missing".
    names = "".join(f"{name}\n" for name in _OPERATION_HEADS)
    output = git.run_optional("cat-file", "--batch-check", stdin=names)
    for kind, line in zip(_OPERATION_HEADS.values(), (output or "").splitlines()):
        if len(line.split()) == 3:
            return InProgressOperation(kind, conflict_count)
    return None


def _rebase_progress(git: GitCli) -> tuple[int, int] | None:
    """(step, total) of a rebase in progress, or ``None`` when there is none.

    ``rebase-merge/`` (the default and interactive backend) records ``msgnum``/``end``;
    ``rebase-apply/`` (the apply backend) records ``next``/``last``, but is also used
    by ``git am``, which marks itself with an ``applying`` file.
    """
    output = git.run_optional(
        "rev-parse", "--path-format=absolute", "--git-path", "rebase-merge", "--git-path", "rebase-apply"
    )
    if output is None:
        return None
    merge_backend, apply_backend = (Path(line) for line in output.splitlines()[:2])
    if merge_backend.is_dir():
        return _number(merge_backend / "msgnum"), _number(merge_backend / "end")
    if apply_backend.is_dir() and not (apply_backend / "applying").exists():
        return _number(apply_backend / "next"), _number(apply_backend / "last")
    return None


def _number(file: Path) -> int:
    """The integer stored in ``file``; 0 if it is missing or unreadable (e.g. mid-write)."""
    try:
        return int(file.read_text().strip())
    except (OSError, ValueError):
        return 0
