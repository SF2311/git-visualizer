"""File transitions: how the Working Tree and Staging Area columns changed between two
Repository Snapshots.

Files are matched by path. A file that left one area and is listed in the other
afterwards *moved* (``add``, ``restore --staged``). When HEAD moved to a newly created
commit (one not shown before, not even as a Ghost Commit), files that left an area
without moving went into that commit (``commit``, ``commit -a``, ``commit --amend``); a
file leaving the Staging Area then counts as committed even if it is still listed in
the Working Tree (a partially staged file).
Everything else appeared or disappeared.
"""

from __future__ import annotations

from collections.abc import Collection
from enum import StrEnum

from git_visualizer.live_view.transitions import Transition, TransitionKind
from git_visualizer.snapshot import RepositorySnapshot


FILE_TRANSITION_KINDS = frozenset(
    {
        TransitionKind.FILE_MOVED,
        TransitionKind.FILE_APPEARED,
        TransitionKind.FILE_DISAPPEARED,
        TransitionKind.FILE_COMMITTED,
    }
)


class Area(StrEnum):
    WORKING_TREE = "workingTree"
    STAGING_AREA = "stagingArea"


def file_transitions(
    previous: RepositorySnapshot, current: RepositorySnapshot, added_commits: Collection[str]
) -> list[Transition]:
    """File transitions in the order the files were listed before, then new arrivals.

    ``added_commits`` are the commits not shown before, not even as Ghost Commits (the
    ``commitAdded`` transitions); only HEAD moving to one of them commits files."""
    before = {
        Area.WORKING_TREE: [entry.path for entry in previous.working_tree],
        Area.STAGING_AREA: [entry.path for entry in previous.staging_area],
    }
    after = {
        Area.WORKING_TREE: {entry.path for entry in current.working_tree},
        Area.STAGING_AREA: {entry.path for entry in current.staging_area},
    }
    new_commit = _new_head_commit(current, added_commits)
    transitions: list[Transition] = []
    arrived: set[tuple[Area, str]] = set()
    for area, other in ((Area.WORKING_TREE, Area.STAGING_AREA), (Area.STAGING_AREA, Area.WORKING_TREE)):
        for path in before[area]:
            if path in after[area]:
                continue
            if new_commit and (area is Area.STAGING_AREA or path not in after[other]):
                transitions.append(
                    Transition(TransitionKind.FILE_COMMITTED, to_hash=new_commit, path=path, from_area=area)
                )
            elif path in after[other]:
                transitions.append(Transition(TransitionKind.FILE_MOVED, path=path, from_area=area, to_area=other))
                arrived.add((other, path))
            else:
                transitions.append(Transition(TransitionKind.FILE_DISAPPEARED, path=path, from_area=area))
    for area, entries in ((Area.WORKING_TREE, current.working_tree), (Area.STAGING_AREA, current.staging_area)):
        listed_before = set(before[area])
        for entry in entries:
            if entry.path not in listed_before and (area, entry.path) not in arrived:
                transitions.append(Transition(TransitionKind.FILE_APPEARED, path=entry.path, to_area=area))
    return transitions


def _new_head_commit(current: RepositorySnapshot, added_commits: Collection[str]) -> str:
    """The commit HEAD moved to if it was just created, else ""."""
    head = current.head.commit_hash
    return head if head is not None and head in added_commits else ""
