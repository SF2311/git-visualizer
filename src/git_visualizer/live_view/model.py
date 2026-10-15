"""The Live View model: the single object QML binds to, and the single test seam.

Interface:

* ``notifyRepositoryChanged()`` — re-read the Observed Repository and update all
  exposed properties (called by the watcher; ``F5`` remains a hidden fallback).
* ``isRepository`` — ``False`` while the observed folder is not (yet) a git
  repository; all History properties are then empty.
* ``repositoryPath`` — the observed folder.
* ``commits`` — list model, one row per commit in the History
  (roles: ``hash``, ``shortHash``, ``subject``, ``column``).
* ``branchLabels`` — list model, one row per local branch
  (roles: ``name``, ``commitHash``, ``column``, ``hasHead``).
* HEAD: ``headBranch`` ("" when detached), ``headCommitHash`` ("" when unborn),
  ``headDetached``, ``headColumn`` (-1 when unborn).
* ``columnCount`` — number of History columns.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from git_visualizer.git_reader import NotARepositoryError, read_snapshot
from git_visualizer.history_layout import commit_columns
from git_visualizer.live_view.list_model import RowListModel
from git_visualizer.snapshot import RepositorySnapshot


class LiveViewModel(QObject):
    headChanged = Signal()
    columnCountChanged = Signal()
    isRepositoryChanged = Signal()

    def __init__(self, repository_path: Path | str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._repository_path = Path(repository_path)
        self._snapshot = RepositorySnapshot.empty()
        self._is_repository = False
        self._columns: dict[str, int] = {}
        self._commits = RowListModel(("hash", "shortHash", "subject", "column"), self)
        self._branch_labels = RowListModel(("name", "commitHash", "column", "hasHead"), self)

    @Slot()
    def notifyRepositoryChanged(self) -> None:
        try:
            snapshot = read_snapshot(self._repository_path)
        except NotARepositoryError:
            self._set_is_repository(False)
            self._apply(RepositorySnapshot.empty())
            return
        self._set_is_repository(True)
        self._apply(snapshot)

    def _set_is_repository(self, is_repository: bool) -> None:
        if is_repository != self._is_repository:
            self._is_repository = is_repository
            self.isRepositoryChanged.emit()

    def _apply(self, snapshot: RepositorySnapshot) -> None:
        self._snapshot = snapshot
        self._columns = commit_columns(snapshot.commits)
        self._commits.set_rows(
            [
                {
                    "hash": commit.hash,
                    "shortHash": commit.short_hash,
                    "subject": commit.subject,
                    "column": self._columns[commit.hash],
                }
                for commit in snapshot.commits
            ]
        )
        self._branch_labels.set_rows(
            [
                {
                    "name": branch.name,
                    "commitHash": branch.commit_hash,
                    "column": self._columns.get(branch.commit_hash, -1),
                    "hasHead": branch.name == snapshot.head.branch_name,
                }
                for branch in snapshot.branches
            ]
        )
        self.headChanged.emit()
        self.columnCountChanged.emit()

    # --- Repository selection ---------------------------------------------------

    def _get_is_repository(self) -> bool:
        return self._is_repository

    isRepository = Property(bool, _get_is_repository, notify=isRepositoryChanged)

    def _get_repository_path(self) -> str:
        return str(self._repository_path)

    repositoryPath = Property(str, _get_repository_path, constant=True)

    # --- History -----------------------------------------------------------------

    def _get_commits(self) -> RowListModel:
        return self._commits

    commits = Property(QObject, _get_commits, constant=True)

    def _get_branch_labels(self) -> RowListModel:
        return self._branch_labels

    branchLabels = Property(QObject, _get_branch_labels, constant=True)

    def _get_column_count(self) -> int:
        return 1 + max(self._columns.values(), default=-1)

    columnCount = Property(int, _get_column_count, notify=columnCountChanged)

    # --- HEAD --------------------------------------------------------------------

    def _get_head_branch(self) -> str:
        return self._snapshot.head.branch_name or ""

    headBranch = Property(str, _get_head_branch, notify=headChanged)

    def _get_head_commit_hash(self) -> str:
        return self._snapshot.head.commit_hash or ""

    headCommitHash = Property(str, _get_head_commit_hash, notify=headChanged)

    def _get_head_detached(self) -> bool:
        return self._snapshot.head.is_detached

    headDetached = Property(bool, _get_head_detached, notify=headChanged)

    def _get_head_column(self) -> int:
        commit_hash = self._snapshot.head.commit_hash
        return self._columns.get(commit_hash, -1) if commit_hash else -1

    headColumn = Property(int, _get_head_column, notify=headChanged)
