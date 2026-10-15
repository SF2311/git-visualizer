"""The Live View model: the single object QML binds to, and the single test seam.

Interface:

* ``LiveViewModel(path, max_commits=30)`` — ``max_commits`` is the display limit N.
* ``notifyRepositoryChanged()`` — re-read the Observed Repository and update all
  exposed properties (called by the manual refresh key, later by the watcher).
* ``commits`` — list model, one row per commit in the History
  (roles: ``hash``, ``shortHash``, ``subject``, ``column``, ``lane``, ``colorIndex``
  (-1 when on no branch), ``isMerge``).
* ``edges`` — list model, one row per parent link (roles: ``childHash``,
  ``parentHash``, ``childColumn``, ``childLane``, ``parentColumn``, ``parentLane``,
  ``colorIndex``, ``toCollapsed``, ``firstParent``). A first-parent edge takes the child's color, other
  parent edges (merges) the parent's. ``toCollapsed`` edges lead to a parent hidden by
  the display limit; they end at column -1 in the child's lane.
* ``branchLabels`` — list model, one row per local branch (roles: ``name``,
  ``commitHash``, ``column``, ``lane``, ``colorIndex``, ``stackIndex``, ``hasHead``).
* ``tagLabels`` — list model, one row per tag (roles: ``name``, ``commitHash``,
  ``column``, ``lane``, ``stackIndex``).
* ``laneBands`` — list model, the stretch of a lane owned by a branch (roles:
  ``lane``, ``branch``, ``colorIndex``, ``firstColumn``, ``lastColumn``).
* ``laneLabelSlots`` — per lane, the most labels stacked on one of its commits.
* HEAD: ``headBranch`` ("" when detached), ``headCommitHash`` ("" when unborn),
  ``headDetached``, ``headColumn``/``headLane`` (-1 when unborn), ``headStackIndex``
  (directly above its branch label when attached, slot 0 on the commit when detached).
* ``columnCount``, ``laneCount``; ``historyTruncated`` and ``hiddenCommitCount`` for
  the collapsed "…" marker of older history.

``colorIndex`` values index ``Theme.branchColors``; a branch keeps its color as long
as it exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from git_visualizer.git_reader import DEFAULT_MAX_COMMITS, read_snapshot
from git_visualizer.history_layout import HistoryLayout, commit_columns, layout_history
from git_visualizer.live_view.branch_colors import BranchColors
from git_visualizer.live_view.list_model import RowListModel
from git_visualizer.snapshot import RepositorySnapshot

NO_COLOR = -1


class LiveViewModel(QObject):
    headChanged = Signal()
    columnCountChanged = Signal()
    historyChanged = Signal()

    def __init__(
        self,
        repository_path: Path | str,
        parent: QObject | None = None,
        *,
        max_commits: int = DEFAULT_MAX_COMMITS,
    ) -> None:
        super().__init__(parent)
        self._repository_path = Path(repository_path)
        self._max_commits = max_commits
        self._snapshot = RepositorySnapshot.empty()
        self._branch_colors = BranchColors()
        self._layout = layout_history(self._snapshot, [])
        self._commits = RowListModel(
            ("hash", "shortHash", "subject", "column", "lane", "colorIndex", "isMerge"), self
        )
        self._edges = RowListModel(
            (
                "childHash",
                "parentHash",
                "childColumn",
                "childLane",
                "parentColumn",
                "parentLane",
                "colorIndex",
                "toCollapsed",
                "firstParent",
            ),
            self,
        )
        self._branch_labels = RowListModel(
            ("name", "commitHash", "column", "lane", "colorIndex", "stackIndex", "hasHead"), self
        )
        self._tag_labels = RowListModel(("name", "commitHash", "column", "lane", "stackIndex"), self)
        self._lane_bands = RowListModel(
            ("lane", "branch", "colorIndex", "firstColumn", "lastColumn"), self
        )

    @Slot()
    def notifyRepositoryChanged(self) -> None:
        self._apply(read_snapshot(self._repository_path, max_commits=self._max_commits))

    def _apply(self, snapshot: RepositorySnapshot) -> None:
        self._snapshot = snapshot
        # New branches are ranked by how far left their tip is: older lines get upper lanes.
        columns = commit_columns(snapshot.commits)
        self._branch_colors.update(
            branch.name
            for branch in sorted(snapshot.branches, key=lambda b: columns.get(b.commit_hash, -1))
        )
        layout = self._layout = layout_history(snapshot, self._branch_colors.ordered_names())

        def commit_color(commit_hash: str) -> int:
            owner = layout.owners.get(commit_hash)
            return NO_COLOR if owner is None else self._branch_colors.color_index(owner)

        self._commits.set_rows(
            [
                {
                    "hash": commit.hash,
                    "shortHash": commit.short_hash,
                    "subject": commit.subject,
                    "column": layout.columns[commit.hash],
                    "lane": layout.lanes[commit.hash],
                    "colorIndex": commit_color(commit.hash),
                    "isMerge": commit.is_merge,
                }
                for commit in snapshot.commits
            ]
        )
        self._edges.set_rows(
            [
                _edge_row(
                    layout,
                    commit.hash,
                    parent,
                    color=commit_color(commit.hash if index == 0 else parent),
                    first_parent=index == 0,
                )
                for commit in snapshot.commits
                for index, parent in enumerate(commit.parents)
            ]
        )
        self._branch_labels.set_rows(
            [
                {
                    "name": branch.name,
                    "commitHash": branch.commit_hash,
                    **_position(layout, branch.commit_hash),
                    "colorIndex": self._branch_colors.color_index(branch.name),
                    "stackIndex": layout.branch_slots[branch.name],
                    "hasHead": branch.name == snapshot.head.branch_name,
                }
                for branch in snapshot.branches
            ]
        )
        self._tag_labels.set_rows(
            [
                {
                    "name": tag.name,
                    "commitHash": tag.commit_hash,
                    **_position(layout, tag.commit_hash),
                    "stackIndex": layout.tag_slots[tag.name],
                }
                for tag in snapshot.tags
            ]
        )
        self._lane_bands.set_rows(
            [
                {
                    "lane": band.lane,
                    "branch": band.branch,
                    "colorIndex": self._branch_colors.color_index(band.branch),
                    "firstColumn": band.first_column,
                    "lastColumn": band.last_column,
                }
                for band in layout.bands
            ]
        )
        self.historyChanged.emit()
        self.headChanged.emit()
        self.columnCountChanged.emit()

    # --- History -----------------------------------------------------------------

    def _get_commits(self) -> RowListModel:
        return self._commits

    commits = Property(QObject, _get_commits, constant=True)

    def _get_edges(self) -> RowListModel:
        return self._edges

    edges = Property(QObject, _get_edges, constant=True)

    def _get_branch_labels(self) -> RowListModel:
        return self._branch_labels

    branchLabels = Property(QObject, _get_branch_labels, constant=True)

    def _get_tag_labels(self) -> RowListModel:
        return self._tag_labels

    tagLabels = Property(QObject, _get_tag_labels, constant=True)

    def _get_lane_bands(self) -> RowListModel:
        return self._lane_bands

    laneBands = Property(QObject, _get_lane_bands, constant=True)

    def _get_column_count(self) -> int:
        return self._layout.column_count

    columnCount = Property(int, _get_column_count, notify=columnCountChanged)

    def _get_lane_count(self) -> int:
        return len(self._layout.lane_label_slots)

    laneCount = Property(int, _get_lane_count, notify=historyChanged)

    def _get_lane_label_slots(self) -> list[int]:
        return list(self._layout.lane_label_slots)

    laneLabelSlots = Property(list, _get_lane_label_slots, notify=historyChanged)

    def _get_history_truncated(self) -> bool:
        return self._snapshot.hidden_commit_count > 0

    historyTruncated = Property(bool, _get_history_truncated, notify=historyChanged)

    def _get_hidden_commit_count(self) -> int:
        return self._snapshot.hidden_commit_count

    hiddenCommitCount = Property(int, _get_hidden_commit_count, notify=historyChanged)

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
        return _position(self._layout, self._snapshot.head.commit_hash)["column"]

    headColumn = Property(int, _get_head_column, notify=headChanged)

    def _get_head_lane(self) -> int:
        return _position(self._layout, self._snapshot.head.commit_hash)["lane"]

    headLane = Property(int, _get_head_lane, notify=headChanged)

    def _get_head_stack_index(self) -> int:
        return self._layout.head_slot

    headStackIndex = Property(int, _get_head_stack_index, notify=headChanged)


def _position(layout: HistoryLayout, commit_hash: str | None) -> dict[str, int]:
    """Column and lane of ``commit_hash``; -1 for both when it is not shown."""
    if commit_hash is None or commit_hash not in layout.columns:
        return {"column": -1, "lane": -1}
    return {"column": layout.columns[commit_hash], "lane": layout.lanes[commit_hash]}


def _edge_row(
    layout: HistoryLayout, child: str, parent: str, *, color: int, first_parent: bool
) -> dict[str, Any]:
    collapsed = parent not in layout.columns
    child_lane = layout.lanes[child]
    return {
        "childHash": child,
        "parentHash": parent,
        "childColumn": layout.columns[child],
        "childLane": child_lane,
        "parentColumn": -1 if collapsed else layout.columns[parent],
        "parentLane": child_lane if collapsed else layout.lanes[parent],
        "colorIndex": color,
        "toCollapsed": collapsed,
        "firstParent": first_parent,
    }
