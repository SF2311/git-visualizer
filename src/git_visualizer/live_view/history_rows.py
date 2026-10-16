"""Rows for the History lists: commits, edges, branch labels, tag labels and lane bands.

A commit takes the color of the branch that owns it in the layout (-1 on no branch); a
Ghost Commit keeps the color it had while it was reachable. A first-parent edge takes
the child's color, a merge's other parent edges the parent's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from git_visualizer.history_layout import HistoryLayout, commit_columns, layout_history
from git_visualizer.live_view.branch_colors import BranchColors
from git_visualizer.live_view.ghost_commits import GhostCommits
from git_visualizer.snapshot import RepositorySnapshot

NO_COLOR = -1

COMMIT_ROLES = ("hash", "shortHash", "subject", "column", "lane", "colorIndex", "isMerge", "isGhost")
EDGE_ROLES = (
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
)
BRANCH_LABEL_ROLES = (
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
)
TAG_LABEL_ROLES = ("name", "commitHash", "column", "lane", "stackIndex")
LANE_BAND_ROLES = ("lane", "branch", "colorIndex", "firstColumn", "lastColumn")


@dataclass(frozen=True)
class HistoryRows:
    commits: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    branch_labels: list[dict[str, Any]]
    tag_labels: list[dict[str, Any]]
    lane_bands: list[dict[str, Any]]

    @property
    def commit_colors(self) -> dict[str, int]:
        """``colorIndex`` per shown commit hash."""
        return {row["hash"]: row["colorIndex"] for row in self.commits}


def lay_out(snapshot: RepositorySnapshot, branch_colors: BranchColors) -> HistoryLayout:
    """Lay out ``snapshot`` after updating ``branch_colors`` for its branches.

    New branches are ranked by how far left their tip is, so older lines get upper lanes.
    """
    columns = commit_columns(snapshot.commits)
    branch_colors.update(
        branch.name for branch in sorted(snapshot.branches, key=lambda b: columns.get(b.commit_hash, -1))
    )
    return layout_history(snapshot, branch_colors.ordered_names())


def history_rows(
    snapshot: RepositorySnapshot, layout: HistoryLayout, branch_colors: BranchColors, ghosts: GhostCommits
) -> HistoryRows:
    """The History rows of ``snapshot`` (which already includes the Ghost Commits)."""

    def commit_color(commit_hash: str) -> int:
        ghost_color = ghosts.color_index(commit_hash)
        if ghost_color is not None:
            return ghost_color
        owner = layout.owners.get(commit_hash)
        return NO_COLOR if owner is None else branch_colors.color_index(owner)

    def is_ghost(commit_hash: str) -> bool:
        return ghosts.color_index(commit_hash) is not None

    commits = [
        {
            "hash": commit.hash,
            "shortHash": commit.short_hash,
            "subject": commit.subject,
            **layout.position(commit.hash).roles(),
            "colorIndex": commit_color(commit.hash),
            "isMerge": commit.is_merge,
            "isGhost": is_ghost(commit.hash),
        }
        for commit in snapshot.commits
    ]
    edges = [
        _edge_row(
            layout,
            commit.hash,
            parent,
            color=commit_color(commit.hash if index == 0 else parent),
            first_parent=index == 0,
            ghost=is_ghost(commit.hash),
        )
        for commit in snapshot.commits
        for index, parent in enumerate(commit.parents)
    ]
    branch_labels = [
        {
            "name": branch.name,
            "commitHash": branch.commit_hash,
            **layout.position(branch.commit_hash).roles(),
            "colorIndex": branch_colors.color_index(branch.name),
            "stackIndex": layout.branch_slots[branch.name],
            "hasHead": branch.name == snapshot.head.branch_name,
            "upstream": branch.upstream or "",
            "ahead": -1 if branch.ahead is None else branch.ahead,
            "behind": -1 if branch.behind is None else branch.behind,
        }
        for branch in snapshot.branches
    ]
    tag_labels = [
        {
            "name": tag.name,
            "commitHash": tag.commit_hash,
            **layout.position(tag.commit_hash).roles(),
            "stackIndex": layout.tag_slots[tag.name],
        }
        for tag in snapshot.tags
    ]
    lane_bands = [
        {
            "lane": band.lane,
            "branch": band.branch,
            "colorIndex": branch_colors.color_index(band.branch),
            "firstColumn": band.first_column,
            "lastColumn": band.last_column,
        }
        for band in layout.bands
    ]
    return HistoryRows(commits, edges, branch_labels, tag_labels, lane_bands)


def _edge_row(
    layout: HistoryLayout, child: str, parent: str, *, color: int, first_parent: bool, ghost: bool
) -> dict[str, Any]:
    """``toCollapsed`` edges lead to a parent hidden by the display limit; they end at
    column -1 in the child's lane."""
    child_position = layout.position(child)
    collapsed = parent not in layout.columns
    parent_position = layout.position(parent) if not collapsed else child_position
    return {
        "childHash": child,
        "parentHash": parent,
        "childColumn": child_position.column,
        "childLane": child_position.lane,
        "parentColumn": -1 if collapsed else parent_position.column,
        "parentLane": parent_position.lane,
        "colorIndex": color,
        "toCollapsed": collapsed,
        "firstParent": first_parent,
        "isGhost": ghost,
    }
