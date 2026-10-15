"""Ghost Commits: commits that were reachable before a state change and are not after.

The rule (spec, ticket 07):

* A commit shown in the previous Repository Snapshot becomes a Ghost Commit when no
  shown ref or HEAD reaches it any more (``refs/stash`` does not count). Commits that
  only dropped out of the display limit are still reachable and do not.
* Ghost Commits are cleared by the next transition that moves a ref
  (:attr:`Transition.moves_ref`); the transition that created them does not clear
  them. Other changes (HEAD only, Working Tree, Staging Area) keep them.
* A Ghost Commit shown again (e.g. checked out) is an ordinary commit again.
* :meth:`GhostCommits.clear` drops them all (``Esc``); a fresh start has none.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from git_visualizer.live_view.transitions import Transition
from git_visualizer.snapshot import Commit, RepositorySnapshot


@dataclass(frozen=True)
class GhostCommit:
    commit: Commit
    color_index: int
    """The color the commit had while it was reachable."""


class GhostCommits:
    def __init__(self) -> None:
        self._ghosts: dict[str, GhostCommit] = {}

    def update(
        self,
        previous: RepositorySnapshot,
        current: RepositorySnapshot,
        transitions: Sequence[Transition],
        *,
        colors: Mapping[str, int],
        unreachable: Callable[[list[str]], set[str]],
    ) -> None:
        """Apply the change ``previous`` → ``current``; ``colors`` are the commits'
        colors as last shown, ``unreachable`` filters hashes no shown ref reaches."""
        shown = {commit.hash for commit in current.commits}
        moves_ref = any(transition.moves_ref for transition in transitions)
        # Older ghosts first: a ghost's parent may only become a ghost later, and the
        # layout walks chains from child to parent.
        kept = {} if moves_ref else {h: g for h, g in self._ghosts.items() if h not in shown}
        candidates = [commit for commit in previous.commits if commit.hash not in shown]
        gone = unreachable([commit.hash for commit in candidates]) if candidates else set()
        kept.update(
            (commit.hash, GhostCommit(commit, colors.get(commit.hash, -1)))
            for commit in candidates  # newest first, children before parents
            if commit.hash in gone
        )
        self._ghosts = kept

    def clear(self) -> None:
        self._ghosts = {}

    @property
    def hashes(self) -> list[str]:
        return list(self._ghosts)

    @property
    def commits(self) -> tuple[Commit, ...]:
        """The Ghost Commits, ordered so that children come before their parents."""
        return tuple(ghost.commit for ghost in self._ghosts.values())

    def color_index(self, commit_hash: str) -> int | None:
        """The ghost's color, or ``None`` if ``commit_hash`` is no Ghost Commit."""
        ghost = self._ghosts.get(commit_hash)
        return None if ghost is None else ghost.color_index
