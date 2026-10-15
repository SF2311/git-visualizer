"""Transition computation: what changed between two Repository Snapshots.

History transitions are computed here; file transitions (Three Areas) in
:mod:`git_visualizer.live_view.file_transitions`.

Only the two snapshots are compared, so a burst of git commands that the watcher
coalesces into one refresh yields just their net difference.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from git_visualizer.snapshot import RepositorySnapshot

TRANSITION_ROLES = ("kind", "refType", "refName", "fromHash", "toHash", "path", "fromArea", "toArea")


class TransitionKind(StrEnum):
    COMMIT_ADDED = "commitAdded"
    """A commit is in the History that was not before (``to_hash``)."""
    REF_ADDED = "refAdded"
    REF_MOVED = "refMoved"
    REF_REMOVED = "refRemoved"
    HEAD_MOVED = "headMoved"
    """HEAD now points at another commit (``from_hash`` is "" when it was unborn)."""
    HEAD_ATTACHED = "headAttached"
    """HEAD is now attached to branch ``ref_name`` (it was detached or on another branch)."""
    HEAD_DETACHED = "headDetached"
    """HEAD was attached to branch ``ref_name`` and is now detached."""
    FILE_MOVED = "fileMoved"
    """File ``path`` left ``from_area`` and is (now or still) listed in ``to_area``."""
    FILE_APPEARED = "fileAppeared"
    """File ``path`` is newly listed in ``to_area``, not moved there from the other area."""
    FILE_DISAPPEARED = "fileDisappeared"
    """File ``path`` is no longer listed in ``from_area`` and went nowhere visible."""
    FILE_COMMITTED = "fileCommitted"
    """File ``path`` left ``from_area`` into the new HEAD commit ``to_hash``."""


class RefType(StrEnum):
    BRANCH = "branch"
    TAG = "tag"


@dataclass(frozen=True)
class Transition:
    kind: TransitionKind
    ref_type: str = ""
    ref_name: str = ""
    from_hash: str = ""
    to_hash: str = ""
    path: str = ""
    from_area: str = ""
    to_area: str = ""

    @property
    def moves_ref(self) -> bool:
        """Whether a ref label (branch or tag) appeared, moved or disappeared."""
        return self.kind in (TransitionKind.REF_ADDED, TransitionKind.REF_MOVED, TransitionKind.REF_REMOVED)

    def file_row(self) -> dict[str, Any]:
        """The roles of a file transition: ``kind``, ``path``, ``fromArea``, ``toArea``, ``toHash``."""
        row = self.row()
        return {role: row[role] for role in ("kind", "path", "fromArea", "toArea", "toHash")}

    def row(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "refType": str(self.ref_type),
            "refName": self.ref_name,
            "fromHash": self.from_hash,
            "toHash": self.to_hash,
            "path": self.path,
            "fromArea": str(self.from_area),
            "toArea": str(self.to_area),
        }


def history_transitions(previous: RepositorySnapshot, current: RepositorySnapshot) -> list[Transition]:
    """Commits added, ref labels added/moved/removed and HEAD changes, in that order."""
    known = {commit.hash for commit in previous.commits}
    transitions = [
        Transition(TransitionKind.COMMIT_ADDED, to_hash=commit.hash)
        for commit in reversed(current.commits)  # oldest first, the order they grow in
        if commit.hash not in known
    ]
    transitions += _ref_transitions(_refs(previous), _refs(current))
    transitions += _head_transitions(previous, current)
    return transitions


def _refs(snapshot: RepositorySnapshot) -> dict[tuple[RefType, str], str]:
    refs = {(RefType.BRANCH, branch.name): branch.commit_hash for branch in snapshot.branches}
    refs.update({(RefType.TAG, tag.name): tag.commit_hash for tag in snapshot.tags})
    return refs


def _ref_transitions(
    before: dict[tuple[RefType, str], str], after: dict[tuple[RefType, str], str]
) -> list[Transition]:
    transitions = []
    for (ref_type, name), target in after.items():
        old = before.get((ref_type, name))
        if old is None:
            transitions.append(Transition(TransitionKind.REF_ADDED, ref_type, name, to_hash=target))
        elif old != target:
            transitions.append(Transition(TransitionKind.REF_MOVED, ref_type, name, old, target))
    for (ref_type, name), old in before.items():
        if (ref_type, name) not in after:
            transitions.append(Transition(TransitionKind.REF_REMOVED, ref_type, name, from_hash=old))
    return transitions


def _head_transitions(previous: RepositorySnapshot, current: RepositorySnapshot) -> list[Transition]:
    before, after = previous.head, current.head
    transitions = []
    if before.commit_hash != after.commit_hash and after.commit_hash is not None:
        transitions.append(
            Transition(TransitionKind.HEAD_MOVED, from_hash=before.commit_hash or "", to_hash=after.commit_hash)
        )
    if after.branch_name is not None and after.branch_name != before.branch_name:
        transitions.append(Transition(TransitionKind.HEAD_ATTACHED, RefType.BRANCH, after.branch_name))
    elif after.branch_name is None and before.branch_name is not None:
        transitions.append(Transition(TransitionKind.HEAD_DETACHED, RefType.BRANCH, before.branch_name))
    return transitions
