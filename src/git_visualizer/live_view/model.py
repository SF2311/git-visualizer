"""The Live View model: the single object QML binds to, and the single test seam.

Interface:

* ``LiveViewModel(path, max_commits=30)`` — ``max_commits`` is the display limit N.
* ``notifyRepositoryChanged()`` — re-read the Observed Repository and update all
  exposed properties (called by the watcher; ``F5`` remains a hidden fallback).
* ``isRepository`` — ``False`` while the observed folder is not (yet) a git
  repository; all History properties are then empty.
* ``repositoryPath`` — the observed folder.
* ``commits`` — list model, one row per commit in the History
  (roles: ``hash``, ``shortHash``, ``subject``, ``column``, ``lane``, ``colorIndex``
  (-1 when on no branch), ``isMerge``, ``isGhost``). Ghost Commits are listed after
  the reachable commits and keep the color they had while reachable.
* ``edges`` — list model, one row per parent link (roles: ``childHash``,
  ``parentHash``, ``childColumn``, ``childLane``, ``parentColumn``, ``parentLane``,
  ``colorIndex``, ``toCollapsed``, ``firstParent``, ``isGhost`` (the child is a Ghost
  Commit)). A first-parent edge takes the child's color, other parent edges (merges) the parent's. ``toCollapsed`` edges lead to a parent hidden by
  the display limit; they end at column -1 in the child's lane.
* ``branchLabels`` — list model, one row per local branch (roles: ``name``,
  ``commitHash``, ``column``, ``lane``, ``colorIndex``, ``stackIndex``, ``hasHead``,
  ``upstream`` ("" without Upstream), ``ahead``/``behind`` (-1 without Upstream or
  when the Upstream's ref is gone)).
* ``remoteTrackingLabels`` — list model, one row per Remote-tracking Branch, keyed by
  name (roles: ``name`` (e.g. ``origin/main``), ``remote``, ``commitHash``,
  ``column``, ``lane``, ``colorIndex`` (its local branch's when it is that branch's
  Upstream, else -1), ``stackIndex``, ``isUpstream``).
* ``remotes`` — list model, one row per Remote box (roles: ``name``, ``url``,
  ``shortUrl``, ``lastFetched`` (Unix seconds, 0 if never fetched),
  ``trackingBranches`` (list of ``{name, colorIndex}``)). ``lastFetchText(lastFetched,
  now)`` renders "zuletzt geholt vor 12 Min.". The Live View never fetches.
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
* ``workingTreeFiles`` / ``stagingAreaFiles`` — list models of changed files only
  (roles: ``path``, ``change`` — one of ``untracked``, ``new``, ``modified``,
  ``deleted``, ``renamed`` —, ``originalPath`` ("" unless renamed), ``conflicted``).
  A partially staged file appears in both. Both are updated row by row, keyed by
  ``path``. The HEAD commit (``headCommitHash``) is
  highlighted in the History as the third area.
* ``transitions`` — list model of what changed between the previous and the current
  snapshot (roles: ``kind``, ``refType``, ``refName``, ``fromHash``, ``toHash``; see
  :class:`~git_visualizer.live_view.transitions.TransitionKind`). Empty after the
  first refresh and after a refresh that changed nothing; a coalesced burst of git
  commands yields only its net difference. ``addedCommitHashes`` lists the hashes of
  its ``commitAdded`` transitions. Both change before the History lists are updated
  and notify ``transitionsChanged``.
* File transitions (ticket 06) are appended to ``transitions`` after the History ones:
  ``fileMoved`` (``fromArea`` → ``toArea``), ``fileAppeared`` (``toArea``),
  ``fileDisappeared`` (``fromArea``) and ``fileCommitted`` (``fromArea`` into the new
  commit ``toHash``), each for one ``path``; areas are ``workingTree`` and
  ``stagingArea`` (roles ``path``, ``fromArea``, ``toArea`` are "" for History
  transitions). ``fileTransitions`` lists the same rows as plain maps (roles ``kind``,
  ``path``, ``fromArea``, ``toArea``, ``toHash``) for the view to start its file
  animations from; see :mod:`git_visualizer.live_view.file_transitions`.
* ``leavingLabels`` — branch, tag and Remote-tracking Branch labels removed by the
  most recent refresh that added, moved or removed a ref (``refType`` ``branch``,
  ``tag`` or ``remoteTracking``), at their last position, for the view to fade out
  (roles: ``refType``, ``name``, ``colorIndex`` (-1 for tags), ``column``, ``lane``,
  ``stackIndex``).

* ``ghostCommitHashes`` — hashes of the Ghost Commits (see
  :mod:`~git_visualizer.live_view.ghost_commits`): commits shown before a refresh that
  no shown ref or HEAD reaches afterwards. They stay in ``commits`` and ``edges``
  (``isGhost``) until the next refresh that moves a ref, or until
  ``clearGhostCommits()`` (``Esc``). None after the first refresh.

The History lists (``commits``, ``edges``, ``branchLabels``, ``tagLabels``,
``laneBands``) are updated row by row, keyed by commit hash, parent link, label name
and lane owner, so that QML delegates persist across refreshes and animate.
* In-progress Operation (merge, rebase, cherry-pick, revert): ``operationKind``
  ("" when none, else ``merge``, ``rebase``, ``cherry-pick`` or ``revert``),
  ``operationStep``/``operationTotal`` (rebase progress, 0 when unknown or not a
  rebase), ``conflictCount`` (unmerged files) and ``operationBanner``, the German
  banner text ("Merge läuft – 2 Konflikte", "Rebase 2/5"; "" when none). Conflicted
  files are listed in ``workingTreeFiles`` with ``conflicted``; during a paused rebase
  HEAD is detached.

``colorIndex`` values index ``Theme.branchColors``; a branch keeps its color as long
as it exists.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from git_visualizer.git_reader import DEFAULT_MAX_COMMITS, NotARepositoryError, read_snapshot
from git_visualizer.history_layout import HistoryLayout, commit_columns, layout_history
from git_visualizer.live_view.branch_colors import BranchColors
from git_visualizer.live_view.file_transitions import FILE_TRANSITION_KINDS, file_transitions
from git_visualizer.live_view.ghost_commits import GhostCommits
from git_visualizer.live_view.list_model import RowListModel
from git_visualizer.live_view.operation_banner import banner_text
from git_visualizer.live_view.remotes import (
    REMOTE_ROLES,
    REMOTE_TRACKING_ROLES,
    last_fetch_text,
    remote_rows,
    remote_tracking_rows,
)
from git_visualizer.live_view.three_areas import FILE_ROLES, file_rows
from git_visualizer.live_view.transitions import (
    TRANSITION_ROLES,
    RefType,
    Transition,
    TransitionKind,
    history_transitions,
)
from git_visualizer.reachability import unreachable_commits
from git_visualizer.snapshot import RepositorySnapshot

NO_COLOR = -1
LEAVING_LABEL_ROLES = ("refType", "name", "colorIndex", "column", "lane", "stackIndex")


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
        self._snapshot = RepositorySnapshot.empty()
        self._branch_colors = BranchColors()
        self._layout = layout_history(self._snapshot, [])
        self._commits = RowListModel(
            ("hash", "shortHash", "subject", "column", "lane", "colorIndex", "isMerge", "isGhost"),
            self,
            key_roles=("hash",),
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
                "isGhost",
            ),
            self,
            key_roles=("childHash", "parentHash"),
        )
        self._branch_labels = RowListModel(
            (
                "name",
                "commitHash",
                "column",
                "lane",
                "colorIndex",
                "stackIndex",
                "hasHead",
                "upstream",
                "ahead",
                "behind",
            ),
            self,
            key_roles=("name",),
        )
        self._tag_labels = RowListModel(
            ("name", "commitHash", "column", "lane", "stackIndex"), self, key_roles=("name",)
        )
        self._lane_bands = RowListModel(
            ("lane", "branch", "colorIndex", "firstColumn", "lastColumn"),
            self,
            key_roles=("lane", "branch"),
        )
        self._has_read = False
        self._ghost_commits = GhostCommits()
        self._shown_commit_colors: dict[str, int] = {}
        self._transitions = RowListModel(TRANSITION_ROLES, self)
        self._added_commit_hashes: list[str] = []
        self._leaving_labels = RowListModel(LEAVING_LABEL_ROLES, self, key_roles=("refType", "name"))
        self._shown_labels: dict[tuple[str, str], dict[str, Any]] = {}
        self._is_repository = False
        self._working_tree_files = RowListModel(FILE_ROLES, self, key_roles=("path",))
        self._staging_area_files = RowListModel(FILE_ROLES, self, key_roles=("path",))
        self._remote_tracking_labels = RowListModel(REMOTE_TRACKING_ROLES, self, key_roles=("name",))
        self._remotes = RowListModel(REMOTE_ROLES, self, key_roles=("name",))
        self._file_transitions: list[dict[str, Any]] = []

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

    def _set_is_repository(self, is_repository: bool) -> None:
        if is_repository != self._is_repository:
            self._is_repository = is_repository
            self.isRepositoryChanged.emit()

    @Slot()
    def clearGhostCommits(self) -> None:
        self._ghost_commits.clear()
        self._show()

    def _apply(self, snapshot: RepositorySnapshot) -> None:
        transitions = history_transitions(self._snapshot, snapshot) if self._has_read else []
        if self._has_read:
            transitions = self._update_ghost_commits(snapshot, transitions)
            transitions = transitions + file_transitions(self._snapshot, snapshot)
        self._has_read = True
        self._set_transitions(transitions)
        self._snapshot = snapshot
        self._show()

    def _update_ghost_commits(
        self, snapshot: RepositorySnapshot, transitions: list[Transition]
    ) -> list[Transition]:
        """Update the Ghost Commits; returns ``transitions`` without ghosts shown again
        as reachable commits (they are already on screen, so they must not grow in)."""
        previous_ghosts = set(self._ghost_commits.hashes)
        self._ghost_commits.update(
            self._snapshot,
            snapshot,
            transitions,
            colors=self._shown_commit_colors,
            unreachable=lambda hashes: unreachable_commits(
                self._repository_path, hashes, head_commit=snapshot.head.commit_hash
            ),
        )
        return [
            transition
            for transition in transitions
            if not (transition.kind is TransitionKind.COMMIT_ADDED and transition.to_hash in previous_ghosts)
        ]

    def _show(self) -> None:
        """Update the exposed lists for ``self._snapshot`` plus the Ghost Commits."""
        ghosts = self._ghost_commits
        snapshot = replace(self._snapshot, commits=self._snapshot.commits + ghosts.commits)
        # New branches are ranked by how far left their tip is: older lines get upper lanes.
        columns = commit_columns(snapshot.commits)
        self._branch_colors.update(
            branch.name
            for branch in sorted(snapshot.branches, key=lambda b: columns.get(b.commit_hash, -1))
        )
        layout = self._layout = layout_history(snapshot, self._branch_colors.ordered_names())

        def commit_color(commit_hash: str) -> int:
            ghost_color = ghosts.color_index(commit_hash)
            if ghost_color is not None:
                return ghost_color
            owner = layout.owners.get(commit_hash)
            return NO_COLOR if owner is None else self._branch_colors.color_index(owner)

        commit_rows: list[dict[str, Any]] = [
            {
                "hash": commit.hash,
                "shortHash": commit.short_hash,
                "subject": commit.subject,
                "column": layout.columns[commit.hash],
                "lane": layout.lanes[commit.hash],
                "colorIndex": commit_color(commit.hash),
                "isMerge": commit.is_merge,
                "isGhost": ghosts.color_index(commit.hash) is not None,
            }
            for commit in snapshot.commits
        ]
        self._commits.set_rows(commit_rows)
        self._shown_commit_colors = {row["hash"]: row["colorIndex"] for row in commit_rows}
        self._edges.set_rows(
            [
                _edge_row(
                    layout,
                    commit.hash,
                    parent,
                    color=commit_color(commit.hash if index == 0 else parent),
                    first_parent=index == 0,
                    ghost=ghosts.color_index(commit.hash) is not None,
                )
                for commit in snapshot.commits
                for index, parent in enumerate(commit.parents)
            ]
        )
        branch_rows = [
            {
                "name": branch.name,
                "commitHash": branch.commit_hash,
                **_position(layout, branch.commit_hash),
                "colorIndex": self._branch_colors.color_index(branch.name),
                "stackIndex": layout.branch_slots[branch.name],
                "hasHead": branch.name == snapshot.head.branch_name,
                "upstream": branch.upstream or "",
                "ahead": -1 if branch.ahead is None else branch.ahead,
                "behind": -1 if branch.behind is None else branch.behind,
            }
            for branch in snapshot.branches
        ]
        tag_rows = [
            {
                "name": tag.name,
                "commitHash": tag.commit_hash,
                **_position(layout, tag.commit_hash),
                "stackIndex": layout.tag_slots[tag.name],
            }
            for tag in snapshot.tags
        ]
        self._branch_labels.set_rows(branch_rows)
        self._tag_labels.set_rows(tag_rows)
        color_of = self._branch_colors.color_index
        tracking_rows = remote_tracking_rows(snapshot, layout, color_of, lambda h: _position(layout, h))
        self._remote_tracking_labels.set_rows(tracking_rows)
        self._remember_shown_labels(branch_rows, tag_rows, tracking_rows)
        self._remotes.set_rows(remote_rows(snapshot, layout, color_of))
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
        self._working_tree_files.set_rows(file_rows(snapshot.working_tree))
        self._staging_area_files.set_rows(file_rows(snapshot.staging_area))
        self.inProgressOperationChanged.emit()
        self.headChanged.emit()
        self.columnCountChanged.emit()

    def _set_transitions(self, transitions: list[Transition]) -> None:
        """Expose ``transitions``; call before the History lists change."""
        if any(transition.moves_ref for transition in transitions):
            self._leaving_labels.set_rows(
                [
                    self._shown_labels[(transition.ref_type, transition.ref_name)]
                    for transition in transitions
                    if transition.kind is TransitionKind.REF_REMOVED
                    and (transition.ref_type, transition.ref_name) in self._shown_labels
                ]
            )
        self._added_commit_hashes = [
            transition.to_hash for transition in transitions if transition.kind is TransitionKind.COMMIT_ADDED
        ]
        self._file_transitions = [
            transition.file_row() for transition in transitions if transition.kind in FILE_TRANSITION_KINDS
        ]
        self._transitions.set_rows([transition.row() for transition in transitions])
        self.transitionsChanged.emit()

    def _remember_shown_labels(
        self,
        branch_rows: list[dict[str, Any]],
        tag_rows: list[dict[str, Any]],
        tracking_rows: list[dict[str, Any]],
    ) -> None:
        """Keep where each label is drawn now, so a removed one can fade out there."""
        labelled = [(RefType.BRANCH, row, row["colorIndex"]) for row in branch_rows]
        labelled += [(RefType.TAG, row, NO_COLOR) for row in tag_rows]
        labelled += [(RefType.REMOTE_TRACKING, row, row["colorIndex"]) for row in tracking_rows]
        self._shown_labels = {
            (str(ref_type), row["name"]): {
                "refType": str(ref_type),
                "name": row["name"],
                "colorIndex": color,
                "column": row["column"],
                "lane": row["lane"],
                "stackIndex": row["stackIndex"],
            }
            for ref_type, row, color in labelled
            if row["column"] >= 0
        }

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

    @Slot(float, float, result=str)
    def lastFetchText(self, last_fetched: float, now: float) -> str:
        """German relative last-fetch time; QML passes ``now`` so the text stays current."""
        return last_fetch_text(last_fetched, now)

    # --- In-progress Operation ---------------------------------------------------

    def _get_operation_kind(self) -> str:
        operation = self._snapshot.in_progress_operation
        return "" if operation is None else operation.kind.value

    operationKind = Property(str, _get_operation_kind, notify=inProgressOperationChanged)

    def _get_operation_step(self) -> int:
        operation = self._snapshot.in_progress_operation
        return 0 if operation is None else operation.step

    operationStep = Property(int, _get_operation_step, notify=inProgressOperationChanged)

    def _get_operation_total(self) -> int:
        operation = self._snapshot.in_progress_operation
        return 0 if operation is None else operation.total

    operationTotal = Property(int, _get_operation_total, notify=inProgressOperationChanged)

    def _get_conflict_count(self) -> int:
        operation = self._snapshot.in_progress_operation
        return 0 if operation is None else operation.conflict_count

    conflictCount = Property(int, _get_conflict_count, notify=inProgressOperationChanged)

    def _get_operation_banner(self) -> str:
        return banner_text(self._snapshot.in_progress_operation)

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
    layout: HistoryLayout, child: str, parent: str, *, color: int, first_parent: bool, ghost: bool
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
        "isGhost": ghost,
    }
