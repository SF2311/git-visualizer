"""The Live View model: the single object QML binds to, and the single test seam.

``LiveViewModel(path, max_commits=30)`` observes the folder ``path``; ``max_commits``
is the display limit N. It is a thin Qt facade: the rows and per-feature state come
from the modules next to it.

Slots
    ``notifyRepositoryChanged()`` re-reads the Observed Repository (called by the
    watcher and by ``F5``); ``clearGhostCommits()`` (``Esc``);
    ``lastFetchText(lastFetched, now)``, e.g. "zuletzt geholt vor 12 Min.".

Repository selection
    ``isRepository`` (``False`` while the folder is not (yet) a repository; everything
    else is then empty) and ``repositoryPath``.

History (:mod:`.history_rows`)
    List models ``commits``, ``edges``, ``branchLabels``, ``tagLabels`` and
    ``laneBands``, updated row by row (keyed by commit hash, parent link, label name and
    lane owner) so that QML delegates persist and animate. ``columnCount``,
    ``laneCount``, ``laneLabelSlots``, ``historyTruncated`` and ``hiddenCommitCount``
    (the collapsed "…" of older history). ``colorIndex`` values index
    ``Theme.branchColors``; -1 means no color.

HEAD
    ``headBranch`` ("" when detached), ``headCommitHash`` ("" when unborn),
    ``headDetached``, ``headColumn``/``headLane`` (-1 when not shown) and
    ``headStackIndex``.

History changes (:mod:`.transitions`, :mod:`.file_transitions`, :mod:`.ghost_commits`,
:mod:`.leaving_labels`)
    ``transitions`` (History transitions, then file transitions; empty after the first
    refresh), ``addedCommitHashes`` and ``fileTransitions``, all notified by
    ``transitionsChanged`` before the History lists change. ``leavingLabels`` are
    removed labels at their last position, to fade out. ``ghostCommitHashes``: Ghost
    Commits stay in ``commits``/``edges`` with ``isGhost`` until the next refresh that
    moves a ref, or until ``clearGhostCommits()``.

Three Areas (:mod:`.three_areas`)
    ``workingTreeFiles`` and ``stagingAreaFiles``, changed files only, keyed by
    ``path``; a partially staged file is in both.

Remotes (:mod:`.remotes`)
    ``remotes`` (one row per Remote box) and ``remoteTrackingLabels``. The Live View
    never fetches.

In-progress Operation (:mod:`.operation_state`)
    ``operationKind``, ``operationStep``, ``operationTotal``, ``conflictCount`` and
    ``operationBanner``, notified by ``inProgressOperationChanged``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from git_visualizer.git_reader import DEFAULT_MAX_COMMITS, NotARepositoryError, read_snapshot
from git_visualizer.history_layout import layout_history
from git_visualizer.live_view.branch_colors import BranchColors
from git_visualizer.live_view.file_transitions import FILE_TRANSITION_KINDS, file_transitions
from git_visualizer.live_view.ghost_commits import GhostCommits
from git_visualizer.live_view.history_rows import (
    BRANCH_LABEL_ROLES,
    COMMIT_ROLES,
    EDGE_ROLES,
    LANE_BAND_ROLES,
    TAG_LABEL_ROLES,
    history_rows,
    lay_out,
)
from git_visualizer.live_view.leaving_labels import LEAVING_LABEL_ROLES, LeavingLabels
from git_visualizer.live_view.list_model import RowListModel
from git_visualizer.live_view.operation_state import OperationState
from git_visualizer.live_view.remotes import (
    REMOTE_ROLES,
    REMOTE_TRACKING_ROLES,
    last_fetch_text,
    remote_rows,
    remote_tracking_rows,
)
from git_visualizer.live_view.three_areas import FILE_ROLES, file_rows
from git_visualizer.live_view.transitions import TRANSITION_ROLES, Transition, TransitionKind, history_transitions
from git_visualizer.reachability import unreachable_commits
from git_visualizer.snapshot import RepositorySnapshot


class LiveViewModel(QObject):
    headChanged = Signal()
    columnCountChanged = Signal()
    historyChanged = Signal()
    isRepositoryChanged = Signal()
    transitionsChanged = Signal()
    inProgressOperationChanged = Signal()

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
        self._is_repository = False
        self._has_read = False
        self._snapshot = RepositorySnapshot.empty()
        self._operation = OperationState()
        self._branch_colors = BranchColors()
        self._layout = layout_history(self._snapshot, [])
        self._ghost_commits = GhostCommits()
        self._leaving = LeavingLabels()
        self._added_commit_hashes: list[str] = []
        self._file_transitions: list[dict[str, Any]] = []

        self._commits = RowListModel(COMMIT_ROLES, self, key_roles=("hash",))
        self._edges = RowListModel(EDGE_ROLES, self, key_roles=("childHash", "parentHash"))
        self._branch_labels = RowListModel(BRANCH_LABEL_ROLES, self, key_roles=("name",))
        self._tag_labels = RowListModel(TAG_LABEL_ROLES, self, key_roles=("name",))
        self._lane_bands = RowListModel(LANE_BAND_ROLES, self, key_roles=("lane", "branch"))
        self._transitions = RowListModel(TRANSITION_ROLES, self)
        self._leaving_labels = RowListModel(LEAVING_LABEL_ROLES, self, key_roles=("refType", "name"))
        self._working_tree_files = RowListModel(FILE_ROLES, self, key_roles=("path",))
        self._staging_area_files = RowListModel(FILE_ROLES, self, key_roles=("path",))
        self._remote_tracking_labels = RowListModel(REMOTE_TRACKING_ROLES, self, key_roles=("name",))
        self._remotes = RowListModel(REMOTE_ROLES, self, key_roles=("name",))

    @Slot()
    def notifyRepositoryChanged(self) -> None:
        try:
            snapshot = read_snapshot(self._repository_path, max_commits=self._max_commits)
        except NotARepositoryError:
            self._set_is_repository(False)
            self._ghost_commits.clear()
            self._apply(RepositorySnapshot.empty())
            return
        self._set_is_repository(True)
        self._apply(snapshot)

    @Slot()
    def clearGhostCommits(self) -> None:
        self._ghost_commits.clear()
        self._show()

    @Slot(float, float, result=str)
    def lastFetchText(self, last_fetched: float, now: float) -> str:
        """German relative last-fetch time; QML passes ``now`` so the text stays current."""
        return last_fetch_text(last_fetched, now)

    def _set_is_repository(self, is_repository: bool) -> None:
        if is_repository != self._is_repository:
            self._is_repository = is_repository
            self.isRepositoryChanged.emit()

    def _apply(self, snapshot: RepositorySnapshot) -> None:
        transitions: list[Transition] = []
        if self._has_read:
            transitions = self._ghost_commits.update(
                self._snapshot,
                snapshot,
                history_transitions(self._snapshot, snapshot),
                unreachable=lambda hashes: unreachable_commits(
                    self._repository_path, hashes, head_commit=snapshot.head.commit_hash
                ),
            )
            added = {t.to_hash for t in transitions if t.kind is TransitionKind.COMMIT_ADDED}
            transitions += file_transitions(self._snapshot, snapshot, added)
        self._has_read = True
        self._set_transitions(transitions)
        self._snapshot = snapshot
        self._operation = OperationState.of(snapshot.in_progress_operation)
        self._show()

    def _set_transitions(self, transitions: list[Transition]) -> None:
        """Expose ``transitions``; call before the History lists change."""
        leaving = self._leaving.removed_by(transitions)
        if leaving is not None:
            self._leaving_labels.set_rows(leaving)
        self._added_commit_hashes = [t.to_hash for t in transitions if t.kind is TransitionKind.COMMIT_ADDED]
        self._file_transitions = [t.file_row() for t in transitions if t.kind in FILE_TRANSITION_KINDS]
        self._transitions.set_rows([transition.row() for transition in transitions])
        self.transitionsChanged.emit()

    def _show(self) -> None:
        """Update the exposed lists for ``self._snapshot`` plus the Ghost Commits."""
        snapshot = self._ghost_commits.shown_with(self._snapshot)
        layout = self._layout = lay_out(snapshot, self._branch_colors)
        history = history_rows(snapshot, layout, self._branch_colors, self._ghost_commits)
        tracking = remote_tracking_rows(snapshot, layout, self._branch_colors.color_index)
        self._ghost_commits.remember_shown_colors(history.commit_colors)
        self._leaving.remember(history.branch_labels, history.tag_labels, tracking)

        self._commits.set_rows(history.commits)
        self._edges.set_rows(history.edges)
        self._branch_labels.set_rows(history.branch_labels)
        self._tag_labels.set_rows(history.tag_labels)
        self._remote_tracking_labels.set_rows(tracking)
        self._remotes.set_rows(remote_rows(snapshot, layout, self._branch_colors.color_index))
        self._lane_bands.set_rows(history.lane_bands)
        self.historyChanged.emit()
        self._working_tree_files.set_rows(file_rows(snapshot.working_tree))
        self._staging_area_files.set_rows(file_rows(snapshot.staging_area))
        self.inProgressOperationChanged.emit()
        self.headChanged.emit()
        self.columnCountChanged.emit()

    # --- History changes ---------------------------------------------------------

    def _get_transitions(self) -> RowListModel:
        return self._transitions

    transitions = Property(QObject, _get_transitions, constant=True)

    def _get_added_commit_hashes(self) -> list[str]:
        return list(self._added_commit_hashes)

    addedCommitHashes = Property(list, _get_added_commit_hashes, notify=transitionsChanged)

    def _get_leaving_labels(self) -> RowListModel:
        return self._leaving_labels

    leavingLabels = Property(QObject, _get_leaving_labels, constant=True)

    def _get_ghost_commit_hashes(self) -> list[str]:
        return self._ghost_commits.hashes

    ghostCommitHashes = Property(list, _get_ghost_commit_hashes, notify=historyChanged)

    def _get_file_transitions(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._file_transitions]

    fileTransitions = Property(list, _get_file_transitions, notify=transitionsChanged)

    # --- Three Areas -------------------------------------------------------------

    def _get_working_tree_files(self) -> RowListModel:
        return self._working_tree_files

    workingTreeFiles = Property(QObject, _get_working_tree_files, constant=True)

    def _get_staging_area_files(self) -> RowListModel:
        return self._staging_area_files

    stagingAreaFiles = Property(QObject, _get_staging_area_files, constant=True)

    # --- Remotes -----------------------------------------------------------------

    def _get_remote_tracking_labels(self) -> RowListModel:
        return self._remote_tracking_labels

    remoteTrackingLabels = Property(QObject, _get_remote_tracking_labels, constant=True)

    def _get_remotes(self) -> RowListModel:
        return self._remotes

    remotes = Property(QObject, _get_remotes, constant=True)

    # --- In-progress Operation ---------------------------------------------------

    def _get_operation_kind(self) -> str:
        return self._operation.kind

    operationKind = Property(str, _get_operation_kind, notify=inProgressOperationChanged)

    def _get_operation_step(self) -> int:
        return self._operation.step

    operationStep = Property(int, _get_operation_step, notify=inProgressOperationChanged)

    def _get_operation_total(self) -> int:
        return self._operation.total

    operationTotal = Property(int, _get_operation_total, notify=inProgressOperationChanged)

    def _get_conflict_count(self) -> int:
        return self._operation.conflict_count

    conflictCount = Property(int, _get_conflict_count, notify=inProgressOperationChanged)

    def _get_operation_banner(self) -> str:
        return self._operation.banner

    operationBanner = Property(str, _get_operation_banner, notify=inProgressOperationChanged)

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
        return self._layout.position(self._snapshot.head.commit_hash).column

    headColumn = Property(int, _get_head_column, notify=headChanged)

    def _get_head_lane(self) -> int:
        return self._layout.position(self._snapshot.head.commit_hash).lane

    headLane = Property(int, _get_head_lane, notify=headChanged)

    def _get_head_stack_index(self) -> int:
        return self._layout.head_slot

    headStackIndex = Property(int, _get_head_stack_index, notify=headChanged)
