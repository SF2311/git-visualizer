"""Immutable Repository Snapshot: the Observed Repository's state at one moment.

Produced by :mod:`git_visualizer.git_reader`; consumed by the layout and the Live View
model. Later tickets extend it with further fields (with defaults), e.g. tags,
Remote-tracking Branches, Remotes, Working Tree / Staging Area entries and the
In-progress Operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Commit:
    hash: str
    parents: tuple[str, ...]
    subject: str

    @property
    def short_hash(self) -> str:
        return self.hash[:7]


@dataclass(frozen=True)
class Branch:
    """A local branch: ``refs/heads/<name>`` pointing at ``commit_hash``."""

    name: str
    commit_hash: str


@dataclass(frozen=True)
class Head:
    """HEAD: attached to ``branch_name``, or detached (``branch_name is None``).

    ``commit_hash`` is ``None`` on an unborn branch (no commits yet).
    """

    branch_name: str | None
    commit_hash: str | None

    @property
    def is_detached(self) -> bool:
        return self.branch_name is None


class ChangeKind(StrEnum):
    """Kind of change of a file in the Working Tree or the Staging Area."""

    UNTRACKED = "untracked"
    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass(frozen=True)
class FileEntry:
    """A changed file listed in the Working Tree or the Staging Area.

    ``original_path`` is set for renames (the path before the rename). ``conflicted``
    marks an unmerged file during an In-progress Operation (listed in the Working Tree).
    """

    path: str
    change: ChangeKind
    original_path: str | None = None
    conflicted: bool = False


@dataclass(frozen=True)
class RepositorySnapshot:
    commits: tuple[Commit, ...]
    branches: tuple[Branch, ...]
    head: Head
    working_tree: tuple[FileEntry, ...] = ()
    staging_area: tuple[FileEntry, ...] = ()

    @classmethod
    def empty(cls) -> RepositorySnapshot:
        return cls(commits=(), branches=(), head=Head(branch_name=None, commit_hash=None))
