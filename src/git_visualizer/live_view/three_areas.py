"""Rows for the Three Areas strip: the Working Tree and Staging Area file columns."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from git_visualizer.snapshot import FileEntry

FILE_ROLES = ("path", "change", "originalPath", "conflicted")


def file_rows(entries: Sequence[FileEntry]) -> list[dict[str, Any]]:
    """One row per changed file; ``change`` is a :class:`ChangeKind` value."""
    return [
        {
            "path": entry.path,
            "change": entry.change.value,
            "originalPath": entry.original_path or "",
            "conflicted": entry.conflicted,
        }
        for entry in entries
    ]
